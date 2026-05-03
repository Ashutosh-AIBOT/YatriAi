---
title: YatriAi
emoji: 🌍
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🌍 Yatra AI — AI-Powered Travel Super-App

> **Scale to 1 Billion** | Java + Python + Node.js + Next.js

Yatra AI is an intelligent travel planning assistant that uses a multi-agent AI architecture to create personalized itineraries. One chatbot collects your preferences through a structured 7-stage conversation, then six specialized sub-agents run in parallel to fetch transport, hotels, food, maps, cabs, and places — all ranked by your preferences.

## 🏗️ Architecture

| Service | Technology | Port |
|---|---|---|
| **Frontend** | Next.js 16 + React | 7860 |
| **Gateway** | Spring Boot 3 + Java 21 | 8080 |
| **Orchestrator** | FastAPI + LangGraph + Groq LLaMA 3.1 | 8001 |
| **Notifications** | Node.js + Socket.io | 3001 |
| **Database** | PostgreSQL + pgvector | 5432 |
| **Cache** | Redis 7 | 6379 |
| **Message Broker** | Apache Kafka (KRaft) | 9092 |

## 🧠 AI Agents

- **Transport Agent** — Flights, trains, buses via Amadeus API
- **Cab Agent** — Ola vs Uber price comparison
- **Hotel Agent** — Booking.com search via RapidAPI
- **Food Agent** — Restaurant discovery via Yelp API
- **Places Agent** — Tourist attractions via Google Places
- **Maps Agent** — Route planning via Google Directions

## 🔒 Security

- JWT authentication with refresh tokens
- BCrypt password hashing
- Rate limiting (Bucket4j + Redis)
- CORS restricted to frontend origin
- All secrets in environment variables — zero hardcoded keys

## 📦 Tech Stack

`Java 21` `Spring Boot 3` `Python 3.10` `FastAPI` `LangGraph` `Groq` `Next.js 16` `React` `Node.js` `Socket.io` `PostgreSQL` `Redis` `Kafka` `Docker`
