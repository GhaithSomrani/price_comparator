#!/bin/bash

###############################################################################
# Ubuntu Setup Script for Price Comparator Project
# This script sets up:
# - MongoDB
# - Python environment with Flask API
# - Scrapy spider environment
# - Node.js with Next.js frontend
# - Automated TunisiaNet scraping every 12 hours
###############################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${GREEN}=== Price Comparator Ubuntu Setup ===${NC}"
echo "Project directory: $PROJECT_DIR"

###############################################################################
# 1. System Update and Dependencies
###############################################################################
echo -e "\n${YELLOW}[1/8] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "\n${YELLOW}[2/8] Installing system dependencies...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    gnupg \
    wget

###############################################################################
# 2. Install MongoDB
###############################################################################
echo -e "\n${YELLOW}[2.5/8] Installing MongoDB...${NC}"

# Check if MongoDB is already installed
if command -v mongod &> /dev/null; then
    echo "MongoDB is already installed"
else
    echo "Installing MongoDB..."
    # Import MongoDB public GPG key
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

    # Create list file for MongoDB
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

    # Update package database
    sudo apt update

    # Install MongoDB
    sudo apt install -y mongodb-org
fi

###############################################################################
# 3. Detect MongoDB Service Name
###############################################################################
echo -e "\n${YELLOW}[2.6/8] Detecting MongoDB service name...${NC}"

MONGO_SERVICE=""
if systemctl list-unit-files | grep -q "^mongod.service"; then
    MONGO_SERVICE="mongod"
    echo "MongoDB service name: mongod"
elif systemctl list-unit-files | grep -q "^mongodb.service"; then
    MONGO_SERVICE="mongodb"
    echo "MongoDB service name: mongodb"
else
    echo -e "${YELLOW}Warning: MongoDB service not found, will try 'mongod'${NC}"
    MONGO_SERVICE="mongod"
fi

###############################################################################
# 4. Start and Enable MongoDB
###############################################################################
echo -e "\n${YELLOW}[2.7/8] Starting MongoDB...${NC}"
sudo systemctl start $MONGO_SERVICE || true
sudo systemctl enable $MONGO_SERVICE
sleep 3

echo "MongoDB status:"
sudo systemctl status $MONGO_SERVICE --no-pager | grep Active || echo "MongoDB may still be starting..."

###############################################################################
# 5. Install Node.js (for Next.js frontend)
###############################################################################
echo -e "\n${YELLOW}[3/8] Installing Node.js and npm...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"

###############################################################################
# 6. Setup Python Virtual Environment for Scrapy
###############################################################################
echo -e "\n${YELLOW}[4/8] Setting up Scrapy environment...${NC}"
cd "$PROJECT_DIR/price_comparator"

if [ -d "venv" ]; then
    echo "Virtual environment already exists, removing old one..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo "Installing Scrapy dependencies..."
pip install --upgrade pip
pip install -r requirement.txt

deactivate
echo "Scrapy environment ready!"

###############################################################################
# 7. Setup Python Environment for Flask API
###############################################################################
echo -e "\n${YELLOW}[5/8] Setting up Flask API environment...${NC}"
cd "$PROJECT_DIR"

if [ -d "venv_api" ]; then
    echo "API virtual environment already exists, removing old one..."
    rm -rf venv_api
fi

python3 -m venv venv_api
source venv_api/bin/activate

echo "Installing Flask API dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

deactivate
echo "Flask API environment ready!"

###############################################################################
# 8. Create Systemd Service for Flask API
###############################################################################
echo -e "\n${YELLOW}[6/8] Creating systemd service for Flask API...${NC}"

# Get current user
CURRENT_USER=$(whoami)

# Create systemd service file with correct MongoDB service name
sudo tee /etc/systemd/system/price-comparator-api.service > /dev/null <<EOF
[Unit]
Description=Price Comparator Flask API
After=network.target ${MONGO_SERVICE}.service
Requires=${MONGO_SERVICE}.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv_api/bin"
ExecStart=$PROJECT_DIR/venv_api/bin/python $PROJECT_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable price-comparator-api.service
sudo systemctl start price-comparator-api.service

sleep 3

echo "Flask API service status:"
sudo systemctl status price-comparator-api.service --no-pager | head -n 15

###############################################################################
# 9. Setup Cron Job for TunisiaNet Scraper (Every 12 Hours)
###############################################################################
echo -e "\n${YELLOW}[7/8] Setting up automated scraping (every 12 hours)...${NC}"

# Create scraper run script
cat > "$PROJECT_DIR/run_tunisianet_scraper.sh" <<'EOF'
#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/price_comparator"

# Activate virtual environment
source venv/bin/activate

# Run the spider
echo "=== Starting TunisiaNet scraper at $(date) ===" >> "$SCRIPT_DIR/scraper.log"
scrapy crawl tunisianet 2>&1 | tee -a "$SCRIPT_DIR/scraper.log"
echo "=== Finished TunisiaNet scraper at $(date) ===" >> "$SCRIPT_DIR/scraper.log"

# Deactivate virtual environment
deactivate
EOF

# Make the script executable
chmod +x "$PROJECT_DIR/run_tunisianet_scraper.sh"

# Add cron job (runs at midnight and noon every day)
CRON_JOB="0 */12 * * * $PROJECT_DIR/run_tunisianet_scraper.sh"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -v "run_tunisianet_scraper.sh"; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "The TunisiaNet scraper will run every 12 hours (at midnight and noon)"
crontab -l | grep "run_tunisianet_scraper.sh"

###############################################################################
# 10. Setup Next.js Frontend (Optional)
###############################################################################
echo -e "\n${YELLOW}[8/8] Setting up Next.js Frontend...${NC}"
if [ -d "$PROJECT_DIR/iTrend-Technology-main" ]; then
    read -p "Do you want to setup the Next.js frontend? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR/iTrend-Technology-main"

        echo "Installing Node.js dependencies..."
        npm install

        echo -e "${GREEN}Frontend setup complete!${NC}"
        echo "To start the frontend development server, run:"
        echo "  cd $PROJECT_DIR/iTrend-Technology-main"
        echo "  npm run dev"
    fi
else
    echo "Frontend directory not found, skipping..."
fi

###############################################################################
# Summary
###############################################################################
echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo -e "\n${GREEN}✓ MongoDB:${NC} Running as '$MONGO_SERVICE' service"
echo -e "${GREEN}✓ Flask API:${NC} Running on http://localhost:5000"
echo -e "${GREEN}✓ Scrapy:${NC} Environment ready"
echo -e "${GREEN}✓ TunisiaNet Scraper:${NC} Scheduled to run every 12 hours"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo "  View API logs:        sudo journalctl -u price-comparator-api.service -f"
echo "  Restart API:          sudo systemctl restart price-comparator-api.service"
echo "  Stop API:             sudo systemctl stop price-comparator-api.service"
echo "  View scraper logs:    tail -f $PROJECT_DIR/scraper.log"
echo "  Run scraper manually: $PROJECT_DIR/run_tunisianet_scraper.sh"
echo "  View cron jobs:       crontab -l"
echo "  MongoDB shell:        mongosh"
echo "  MongoDB status:       sudo systemctl status $MONGO_SERVICE"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "  1. Check API is running: curl http://localhost:5000/products"
echo "  2. Run initial scrape:   $PROJECT_DIR/run_tunisianet_scraper.sh"
echo "  3. Monitor the logs to ensure everything works correctly"

echo -e "\n${GREEN}Setup completed successfully!${NC}"
