---
title: puppet 
colorTo: indigo
app_file: backend/backend.py
sdk: gradio
sdk_version: 3.36.1
python_version: 3.11.2
pinned: false
license: mit
---

This is a (soon) 3 part system
- puppet can recieve commands and execute them. 
- backend which collects browser telemetry along with operating system telemetry at a fine grained level. Either android accesibility commands or web dom.
- backend can also send commands for local LLMs to be executed on the puppet llm
- There's a seperate client built on top of gradio included in puppet that we can access via our ios plugin which collects browser telemetry

## Todo Soon

- Browser history interface
- Better docs
- Switching to github for issue planning
