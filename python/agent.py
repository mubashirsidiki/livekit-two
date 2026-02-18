import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    Agent,
    ChatContext,
    inference,
    room_io,
    RunContext,
    function_tool,
    ConversationItemAddedEvent,
    llm
)
from livekit.plugins import noise_cancellation, silero
from livekit.api import UpdateRoomMetadataRequest, LiveKitAPI
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import CONFIG
from core.logging.logger import LOG
from core.services import session_service, knowledge_base_service
from core.models import InitiationMode, CallClassification, CallMetadata
from core.clients import backend_client


load_dotenv('.env.local')


class Assistant(Agent):
    def __init__(self, instructions: str | None = None, chat_ctx: llm.ChatContext | None = None,) -> None:
        default_instructions = """
You are a helpful, friendly voice AI assistant with a warm and engaging personality.
You assist users with their questions and requests using your extensive knowledge.
Keep your responses concise, natural, and conversational.
Avoid complex formatting, emojis, or special punctuation.
Your first message should always be: 'Hello! How can I help you today?'
If the user asks to end the call or says goodbye, call the end_conversation tool.
Do not say goodbye yourself — the tool will speak and end the call.
Note: If the user doesn't respond for 5 seconds, you will prompt them.
If they remain silent for 10 seconds total, end the call with end call function.
"""
        super().__init__(
            instructions=instructions or default_instructions,
            chat_ctx=chat_ctx,
        )

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: str,
    ):
        """End the current call/conversation.
        Always speak a farewell message to the user before calling this function.

        Args:
            reason: The reason for ending the call
            final_message: The farewell message spoken to the user
        """

        context.session.shutdown(drain=True)

        return {'status': 'call_ended', 'reason': reason}


def kb_tool_wrapper(access_token: str, agent_id: int):
    @function_tool
    async def kb_search(context: RunContext, query: str):
        # Search the knowledge base for relevant information based on user query. Use detailed, specific queries that capture the full context of what the user is asking about
        """When user says knowledge base.

        Args:
            query: A detailed and specific search query that captures the full context of what the user is asking about.
        """

        LOG.info('kb is called')

        if not query:
            return {"result": "Please provide a specific question or topic."}

        try:
            results = await knowledge_base_service.search(
                access_token=access_token,
                query=query,
                agent_id=agent_id,
                limit=CONFIG.knowledge_base_search_limit,
            )

            if results:
                formatted = "\n\n".join(
                    [
                        f"Source {i+1} (Score: {r['similarity_score']:.2f}):\n{r['content']}"
                        for i, r in enumerate(results)
                    ]
                )
                return {"result": f"Here's what I found:\n\n{formatted}"}
            return {"result": "I couldn't find specific information about that topic."}
        except Exception as e:
            LOG.error(f"RAG search failed: {e}")
            return {
                "result": "Sorry, I encountered an error searching the knowledge base."
            }

    return kb_search


def _build_transcript(chat_ctx: ChatContext) -> str:
    items = [
        f"{item.role}: {item.text_content}"
        for item in chat_ctx.items
        if item.type == "message"
        and item.role in ("user", "assistant")
        and not item.extra.get("is_summary")
        and item.text_content
    ]
    return "\n".join(items)


async def _extract_call_metadata(
    summarizer: inference.LLM, chat_ctx: ChatContext
) -> CallClassification | None:
    transcript = _build_transcript(chat_ctx)
    if not transcript:
        return None

    classification_ctx = ChatContext()
    classification_ctx.add_message(
        role="system",
        content=(
            "Analyze this phone call transcript and extract:\n"
            "1. is_spam: SPAM if sales/marketing, NOT_SPAM if legitimate inquiry, NOT_SURE if unclear\n"
            "2. reason_for_call: Brief reason the caller contacted\n"
            "3. callback_required: YES if caller needs follow-up, NO if resolved, NOT_SURE if unclear\n"
            "4. callback_required_reason: Why callback is or isn't needed\n"
            "5. caller_name: Name if provided, else None\n"
            "6. calendar_event: If caller mentioned scheduling, extract title, description, start_time, end_time\n\n"
            "Be precise. Use None for unknown values."
        ),
    )
    classification_ctx.add_message(role="user", content=transcript)

    try:
        async with summarizer.chat(
            chat_ctx=classification_ctx,
            response_format=CallClassification,
        ) as stream:
            full_content = ""
            async for chunk in stream:
                if chunk.delta and chunk.delta.content:
                    full_content += chunk.delta.content

            if full_content:
                return CallClassification.model_validate_json(full_content)
    except Exception as e:
        LOG.error(f"Failed to extract call metadata: {e}")

    return None


async def _on_session_end(
    ctx: agents.JobContext,
    access_token: str,
    agent_id: int,
    call_duration: int,
) -> None:
    LOG.info('end session reached!!!!!!!!!!!')

    LOG.info(f'call duration: {call_duration['seconds']}')

    report = ctx.make_session_report()
    summarizer = inference.LLM(model="google/gemini-2.5-flash")

    classification = await _extract_call_metadata(summarizer, report.chat_history)

    LOG.info('end session reached!!!!!!!!!!!')

    if classification:
        LOG.info(f"Call Classification: {classification.model_dump_json()}")

        metadata = CallMetadata(
            datetime=datetime.now(),
            call_transcript=_build_transcript(report.chat_history),
            is_spam=classification.is_spam,
            reason_for_call=classification.reason_for_call,
            callback_required=classification.callback_required,
            callback_required_reason=classification.callback_required_reason,
            caller_name=classification.caller_name,
            calendar_event=classification.calendar_event,
            service_pricing=classification.service_pricing,
            call_duration=round(call_duration['seconds'])
        )

        if CONFIG.backend_url and access_token:
            await backend_client.send_call_analytics(
                access_token, 
                metadata
            )
    else:
        LOG.info("No classification generated for session")


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    participant = await ctx.wait_for_participant()
    LOG.info(f'attributes, {participant.attributes}')

    LOG.info(f'ctx room, {ctx.room.name}')
    LOG.info(f'participant. {participant.sid} {participant.identity} {participant.name}')

    
    LOG.info(f'participant kind: {participant.kind}')

    # if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP and participant.attributes.get('sip.callStatus') == 'dialing':
    #     return

    access_token = participant.attributes.get("accessToken")
    agent_id = int(participant.attributes.get("agentId"))

    LOG.info(f'Agent: {rtc.ParticipantKind.PARTICIPANT_KIND_AGENT}')
    LOG.info(f'Connector: {rtc.ParticipantKind.PARTICIPANT_KIND_CONNECTOR}')
    LOG.info(f'Egress: {rtc.ParticipantKind.PARTICIPANT_KIND_EGRESS}')
    LOG.info(f'Ingress: {rtc.ParticipantKind.PARTICIPANT_KIND_INGRESS}')
    LOG.info(f'Standard: {rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD}')
    LOG.info(f'SIP: {rtc.ParticipantKind.PARTICIPANT_KIND_SIP}')

    LOG.info('participant attributes has been fetched')

    call_duration = {
        'seconds': 0
    }
    
    async def shutdown_callback():
        await _on_session_end(
            ctx, 
            access_token, 
            agent_id,
            call_duration,
        )

    ctx.add_shutdown_callback(shutdown_callback)

    config = await session_service.setup_session(access_token, agent_id)
    instructions = config.get("instructions")

    voice_model = config.get("voiceModelName", "Craig")

    LOG.info('agent has been initialized')

    session = AgentSession(
        stt=inference.STT("deepgram/nova-2-phonecall", language="en"),
        llm=inference.LLM("google/gemini-2.5-flash"),
        tts=inference.TTS(
            "inworld/inworld-tts-1.5-max", language="en", voice='Craig',
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(instructions=instructions),
        room_options=room_io.RoomOptions(
            delete_room_on_close=True,
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    call_started_at = datetime.now(tz=timezone.utc)

    if config.get('knowledgeBaseTrigger', False):
        await session.current_agent.update_tools(
            session.current_agent.tools + [kb_tool_wrapper(access_token, agent_id)]
        )

    user_timestamp = datetime.now(tz=timezone.utc)

    @session.on("conversation_item_added")
    def on_conversation_item_added(ev: ConversationItemAddedEvent):
        nonlocal user_timestamp
        if ev.item.role == 'user':
            user_timestamp = datetime.now(tz=timezone.utc)
        LOG.info(f"[Chat] {ev.item.role}: {ev.item.content}")

    async def silence_check():
        LOG.info('added async loop for silence check')
        while True:
            await asyncio.sleep(5.0)
            current_timestamp = datetime.now(tz=timezone.utc)
            diff_seconds = (current_timestamp - user_timestamp).total_seconds()

            if diff_seconds >= 10:
                await session.generate_reply(
                    instructions="Exactly say this and nothing else, 'Thankyou for your time'",
                    allow_interruptions=True,
                    
                )
                session.shutdown(drain=True)
                break
            elif diff_seconds >= 5:

                await session.generate_reply(
                    instructions="Exactly say this and nothing else, 'Are you still there?'",
                    allow_interruptions=True,
                )

    timer = asyncio.create_task(silence_check())

    @session.on('close')
    def stop_tasks():
        nonlocal call_duration
        call_ended_at = datetime.now(tz=timezone.utc)
        call_duration["seconds"] = (call_ended_at - call_started_at).total_seconds()

        if timer:
            timer.cancel()
            LOG.info('timer removed')

    initiation_mode = config.get("initiationMode", InitiationMode.ai_initiates_dynamic)
    initial_message = config.get("initialMessage")

    LOG.info(f'hhhh {initiation_mode}, {initial_message}')

    if initiation_mode == InitiationMode.ai_initiates_defined and initial_message:
        await session.generate_reply(
            instructions=initial_message,
            allow_interruptions=True,
        )
    elif initiation_mode == InitiationMode.ai_initiates_dynamic:
        await session.generate_reply(
            instructions="Hello! How can I help you today?",
            allow_interruptions=True,
        )


if __name__ == "__main__":
    agents.cli.run_app(server)
