import asyncio
import json
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def main():
  livekit_api = api.LiveKitAPI()

  # Create a dispatch rule to place all callers in the same roo

  request = api.CreateAgentDispatchRequest(
    agent_name='outbound-caller',
    metadata=json.dumps({
      'phone_number': '+447426984363',
      'transfer_to': '+447426984363',
    }),
    room=str(uuid.uuid4()),
  )

  try:
    dispatchRule = await livekit_api.agent_dispatch.create_dispatch(request)
    print(f"Successfully created {dispatchRule}")
  except api.twirp_client.TwirpError as e:
    print(f"{e.code} error: {e.message}")

  await livekit_api.aclose()

asyncio.run(main())