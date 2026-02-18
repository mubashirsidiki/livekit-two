# LiveKit Voice Agent

A real-time conversational voice AI built with LiveKit Agents (Python) and LiveKit Cloud.

You can talk to this agent from the terminal, browser, or phone.

## What This Project Uses

This agent is built with a standard STT → LLM → TTS voice pipeline powered by LiveKit Inference.

- **Speech-to-Text:** Deepgram Nova-2 Phonecall
- **Language Model:** Google Gemini 2.5 Flash
- **Text-to-Speech:** Inworld TTS 1.5 Max (voice: Craig)
- **Voice Activity Detection:** Silero
- **Turn Detection:** Multilingual model

All models run through LiveKit's managed inference layer.

## Key Features

- **Real-time Voice Conversations:** Natural speech interactions with low latency
- **Call Analytics:** Automatic call classification (spam detection, callback requirements, reason for call)
- **Silence Detection:** Auto-prompts after 5s silence, ends call after 10s
- **Noise Cancellation:** BVC for regular calls, BVC Telephony for SIP calls
- **Interruption Support:** Users can interrupt the agent naturally
- **Turn Detection:** Smart detection of when to respond

## Prerequisites

- Python 3.10 – 3.13
- uv package manager
- A free LiveKit Cloud account (note: allows only one free deployment)

---

## LiveKit Cloud Setup

### Install CLI

**Windows:**
```bash
winget install LiveKit.LiveKitCLI
```

### Authenticate

```bash
lk cloud auth
```

This opens a browser where you log in to LiveKit Cloud and select/create a project.

After authentication, run the following command to automatically create a `.env.local` file with the correct credentials:

```bash
lk app env -w
```

Creates `.env.local` with:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `NEXT_PUBLIC_LIVEKIT_URL`
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`

### Deploy

**First time:**
```bash
lk agent create
```

This command will prompt you to select or confirm:
- The project on LiveKit Cloud
- The local project
- The TOML configuration file
- The environment file

Upon successful creation, it will automatically create `livekit.toml` with project subdomain and agent ID, and ask if you want to view logs (recommended to check build status). Example output:
```
Build completed - You can view build logs later with `lk agent logs --log-type=build`
Tailing runtime logs...safe to exit at any time
Waiting for deployment to start...
```

**Updates:**
```bash
lk agent deploy
```

As you make changes locally, run this command to sync them to the deployed agent. It only syncs changes; no need to run `lk agent create` again.

After successful deployment, test your deployed agent at [Agents Playground](https://agents-playground.livekit.io/).

To view your projects and agents, visit [LiveKit Cloud](https://cloud.livekit.io).

For general documentation, see [LiveKit Docs](https://docs.livekit.io/intro/overview/).

---

## Local Development

### Install Dependencies

```bash
uv sync
```

### Download Model Files

```bash
uv run agent.py download-files
```

### Run the Agent

**Console mode (local terminal):**
```bash
uv run agent.py console
```

**Dev mode (connects to LiveKit Cloud):**
```bash
uv run agent.py dev
```

**Production mode:**
```bash
uv run agent.py start
```

---

## Agent Behavior

- Greets users with "Hello! How can I help you today?" when they connect
- Responds to natural speech in real time
- Supports interruptions and turn-taking
- Automatic silence detection:
  - After 5 seconds: Prompts "Are you still there?"
  - After 10 seconds: Says "Thank you for your time" and ends call
- Call classification and analytics on session end
- Room lifecycle is managed by LiveKit Cloud

## Project Structure

```
python/
├── agent.py                 # Main agent entry point
├── core/
│   ├── logging/            # Logging infrastructure
│   ├── models/             # Data models (CallClassification, CallMetadata)
│   └── utils/              # Utility functions
├── livekit.toml            # LiveKit configuration
├── pyproject.toml          # Python dependencies
└── .env.example            # Environment variables template
```

## Cost Analysis

<img width="913" height="636" alt="image" src="https://github.com/user-attachments/assets/00b2a3ae-5d86-4b9f-971f-02c9c1773892" />

For pricing details, see [LiveKit Pricing](https://livekit.io/pricing) and [Inference Pricing](https://livekit.io/pricing/inference).

## LiveKit CLI Project Management

Use `lk project` commands to manage LiveKit projects via CLI. For full details, see [LiveKit Docs: Project Management](https://docs.livekit.io/intro/basics/cli/projects).

### Key Commands

- `lk cloud auth`: Authenticate and link LiveKit Cloud projects.
- `lk project add`: Add a new project manually.
- `lk project list`: List configured projects.
- `lk project remove`: Remove a project.
- `lk project set-default`: Set default project.
