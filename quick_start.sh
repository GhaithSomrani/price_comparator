#!/bin/bash

###############################################################################
# Quick Start Script - After Initial Setup
# Use this script to quickly start all services after a reboot
###############################################################################

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Quick Start - Price Comparator ===${NC}\n"

# Start MongoDB
echo -e "${YELLOW}Starting MongoDB...${NC}"
sudo systemctl start mongodb
sleep 2

# Start Flask API
echo -e "${YELLOW}Starting Flask API...${NC}"
sudo systemctl start price-comparator-api.service
sleep 2

# Check status
echo -e "\n${GREEN}=== Service Status ===${NC}"

if systemctl is-active --quiet mongodb; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB failed to start${NC}"
fi

if systemctl is-active --quiet price-comparator-api.service; then
    echo -e "${GREEN}✓ Flask API is running on http://localhost:5000${NC}"
else
    echo -e "${RED}✗ Flask API failed to start${NC}"
    echo -e "${YELLOW}Check logs: sudo journalctl -u price-comparator-api.service -n 20${NC}"
fi

# Test API
echo -e "\n${YELLOW}Testing API connection...${NC}"
if curl -s -f http://localhost:5000/products > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding${NC}"

    # Get product count
    PRODUCT_COUNT=$(mongosh product_comparator --quiet --eval "db.products.countDocuments()" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database contains $PRODUCT_COUNT products${NC}"
    fi
else
    echo -e "${RED}✗ API is not responding${NC}"
fi

echo -e "\n${GREEN}Quick start complete!${NC}"
echo -e "\nUseful commands:"
echo -e "  View API logs:     ${YELLOW}sudo journalctl -u price-comparator-api.service -f${NC}"
echo -e "  Run scraper:       ${YELLOW}./run_tunisianet_scraper.sh${NC}"
echo -e "  Manage services:   ${YELLOW}./manage_services.sh${NC}"
echo -e "  Test API:          ${YELLOW}curl http://localhost:5000/products${NC}"
