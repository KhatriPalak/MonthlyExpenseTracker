#!/bin/bash

# Monthly Expense Tracker - Startup Script
# This script starts both backend and frontend servers

echo "🚀 Monthly Expense Tracker - Starting Application"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ Node.js/npm is not installed${NC}"
    exit 1
fi

if ! command_exists psql; then
    echo -e "${RED}❌ PostgreSQL is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Update frontend URLs
echo -e "\n${YELLOW}🔧 Updating frontend URLs...${NC}"
python3 update_frontend_urls.py

# Kill any existing processes on ports
echo -e "\n${YELLOW}🔫 Killing existing processes on ports 5002 and 3000...${NC}"
lsof -ti:5002 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Start backend
echo -e "\n${YELLOW}🔥 Starting backend server...${NC}"
cd backend/app
python3 app_integrated.py &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
sleep 3

# Test backend
if curl -s http://localhost:5002/api/test-db > /dev/null; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:5002${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo -e "\n${YELLOW}🎨 Starting frontend server...${NC}"
cd ../../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend in background
npm start &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started with PID: $FRONTEND_PID${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup INT

# Display running status
echo -e "\n${GREEN}=================================================="
echo "✨ Application is running!"
echo "=================================================="
echo "📊 Backend API: http://localhost:5002"
echo "🌐 Frontend UI: http://localhost:3000"
echo "=================================================="
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop both servers"
echo -e "${NC}"

# Keep script running
wait