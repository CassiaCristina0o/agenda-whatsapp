#!/bin/bash
# Atualiza o webhook da Evolution quando o IP local da maquina muda.

EVOLUTION_URL="http://localhost:8080"
INSTANCE="agenda-whatsapp"
API_KEY_FILE="$(dirname "$(readlink -f "$0")")/.env"
PORTA=8000

apikey() {
    grep -m1 '^EVOLUTION_API_KEY=' "$API_KEY_FILE" | cut -d'=' -f2-
}

ip_atual() {
    ip -4 -o addr show scope global 2>/dev/null \
        | grep -v ' docker0\| br-\| veth' \
        | awk '{print $4}' | cut -d/ -f1 | head -n1
}

while true; do
    ip_agora=$(ip_atual)

    if [ -n "$ip_agora" ]; then
        url_configurada=$(curl -s "$EVOLUTION_URL/webhook/find/$INSTANCE" \
            -H "apikey: $(apikey)" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

        if [ "$url_configurada" != "http://$ip_agora:$PORTA/webhook" ]; then
            echo "[$(date '+%F %T')] Webhook desatualizado (estava: $url_configurada) - ajustando para IP atual $ip_agora..."

            curl -s -X POST "$EVOLUTION_URL/webhook/set/$INSTANCE" \
                -H "apikey: $(apikey)" \
                -H "Content-Type: application/json" \
                -d "{\"webhook\":{\"url\":\"http://$ip_agora:$PORTA/webhook\",\"enabled\":true,\"events\":[\"MESSAGES_UPSERT\"],\"webhookByEvents\":false,\"webhookBase64\":false}}" \
                > /dev/null

            echo "[$(date '+%F %T')] Webhook atualizado para http://$ip_agora:$PORTA/webhook"
        fi
    fi

    sleep 15
done
