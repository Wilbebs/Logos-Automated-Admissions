# Logos University - Automated Class Placement System

Automated student classification system using Gemini AI.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with API keys
3. Deploy to Railway.app

## Webhook Endpoint
`POST /webhook/machform`

## System Flow
MachForm → Webhook → Gemini AI → DOCX Report → Email