#!/bin/bash

###############################################################################
# Service Management Script for Price Comparator
# This script provides easy controls for managing all services
###############################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_menu() {
    echo -e "\n${GREEN}=== Price Comparator Service Manager ===${NC}"
    echo -e "${BLUE}1.${NC} Start all services"
    echo -e "${BLUE}2.${NC} Stop all services"
    echo -e "${BLUE}3.${NC} Restart all services"
    echo -e "${BLUE}4.${NC} Check status of all services"
    echo -e "${BLUE}5.${NC} View Flask API logs"
    echo -e "${BLUE}6.${NC} View scraper logs"
    echo -e "${BLUE}7.${NC} Run TunisiaNet scraper now"
    echo -e "${BLUE}8.${NC} Run MyTek scraper now"
    echo -e "${BLUE}9.${NC} View cron schedule"
    echo -e "${BLUE}10.${NC} Test MongoDB connection"
    echo -e "${BLUE}11.${NC} Test Flask API endpoints"
    echo -e "${BLUE}0.${NC} Exit"
    echo -e "${GREEN}=======================================${NC}"
}

start_services() {
    echo -e "\n${YELLOW}Starting all services...${NC}"
    sudo systemctl start mongodb
    sudo systemctl start price-comparator-api.service
    echo -e "${GREEN}✓ All services started${NC}"
}

stop_services() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    sudo systemctl stop price-comparator-api.service
    sudo systemctl stop mongodb
    echo -e "${GREEN}✓ All services stopped${NC}"
}

restart_services() {
    echo -e "\n${YELLOW}Restarting all services...${NC}"
    sudo systemctl restart mongodb
    sudo systemctl restart price-comparator-api.service
    echo -e "${GREEN}✓ All services restarted${NC}"
}

check_status() {
    echo -e "\n${YELLOW}=== MongoDB Status ===${NC}"
    sudo systemctl status mongodb --no-pager | head -n 10

    echo -e "\n${YELLOW}=== Flask API Status ===${NC}"
    sudo systemctl status price-comparator-api.service --no-pager | head -n 10
}

view_api_logs() {
    echo -e "\n${YELLOW}Viewing Flask API logs (Ctrl+C to exit)...${NC}"
    sudo journalctl -u price-comparator-api.service -f
}

view_scraper_logs() {
    echo -e "\n${YELLOW}Viewing scraper logs (Ctrl+C to exit)...${NC}"
    if [ -f "$SCRIPT_DIR/scraper.log" ]; then
        tail -f "$SCRIPT_DIR/scraper.log"
    else
        echo -e "${RED}No scraper logs found${NC}"
    fi
}

run_tunisianet() {
    echo -e "\n${YELLOW}Running TunisiaNet scraper...${NC}"
    "$SCRIPT_DIR/run_tunisianet_scraper.sh"
    echo -e "${GREEN}✓ Scraper finished${NC}"
}

run_mytek() {
    echo -e "\n${YELLOW}Running MyTek scraper...${NC}"
    cd "$SCRIPT_DIR/price_comparator"
    source venv/bin/activate
    scrapy crawl mytek
    deactivate
    echo -e "${GREEN}✓ Scraper finished${NC}"
}

view_cron() {
    echo -e "\n${YELLOW}Current cron schedule:${NC}"
    crontab -l | grep -E "(run_tunisianet|run_mytek|scraper)" || echo "No scraper cron jobs found"
}

test_mongodb() {
    echo -e "\n${YELLOW}Testing MongoDB connection...${NC}"
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB is running and accessible${NC}"
        mongosh product_comparator --eval "db.products.countDocuments()" --quiet
    else
        echo -e "${RED}✗ MongoDB connection failed${NC}"
    fi
}

test_api() {
    echo -e "\n${YELLOW}Testing Flask API endpoints...${NC}"

    echo -e "\n${BLUE}1. Testing /products endpoint:${NC}"
    curl -s http://localhost:5000/products | head -n 5

    echo -e "\n\n${BLUE}2. Testing /filter endpoint:${NC}"
    curl -s http://localhost:5000/filter | head -n 5

    echo -e "\n\n${BLUE}3. Testing /stats endpoint:${NC}"
    curl -s http://localhost:5000/stats | head -n 5

    echo -e "\n${GREEN}✓ API tests completed${NC}"
}

# Main loop
while true; do
    show_menu
    read -p "Select an option: " choice

    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) check_status ;;
        5) view_api_logs ;;
        6) view_scraper_logs ;;
        7) run_tunisianet ;;
        8) run_mytek ;;
        9) view_cron ;;
        10) test_mongodb ;;
        11) test_api ;;
        0) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac

    read -p "Press Enter to continue..."
done
