---
name: oci-server-ops
description: >-
  Especializada em administração, otimização e diagnóstico de servidores Linux em instâncias de baixo
  custo/recurso (como Oracle Cloud Always Free 1GB RAM), execução de Minecraft Bedrock Dedicated Server (BDS),
  gerenciamento de Swap, firewall (iptables/OCI Security Lists) e resolução de rotas UDP e Cloudflare DNS.
---

# OCI Server Ops & Game Server Administration

Guia técnico e operacional para provisionar, diagnosticar e manter servidores de jogos (Minecraft Bedrock) e aplicações Linux em instâncias com recursos restritos (1 GB RAM, Oracle Cloud Infrastructure).

---

## 🎯 Quando Usar

- Configurar ou otimizar instâncias Linux Always Free da Oracle Cloud (OCI).
- Diagnosticar falhas de conectividade UDP/TCP no Minecraft Bedrock (`RakNet` vs `NetherNet`).
- Tratar contenção de memória, congelamentos do Linux e falhas de *OOM Killer* via Swap e `server.properties`.
- Configurar regras de rede no painel OCI (Security Lists), firewall interno (`iptables`/`ufw`) e DNS Cloudflare (Proxy vs DNS-only).
- Gerenciar jogadores, permissões (`permissions.json`) e allowlist (`allowlist.json`) no Minecraft BDS.

---

## 💾 1. Operações de Memória & Prevenção de OOM

Em máquinas com 1 GB de RAM executando múltiplas pilhas (ex: Python/Django/Redis + Minecraft BDS), o Swap é mandatório.

### Protocolo de Ativação do Swap (2 GB)
```bash
# Verificar estado atual
free -h

# Criar arquivo de Swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Persistência pós-reboot
grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Otimizações no `server.properties`
Evite que o Minecraft sature a CPU e a RAM limitando a distância de renderização e threads:
```properties
view-distance=6
tick-distance=4
max-threads=2
max-players=4
```

---

## 🌐 2. Diagnóstico e Resolução de Rede & UDP

O Minecraft Bedrock opera nativamente na porta `19132 UDP`.

### Checklist de Rede Ponta a Ponta:
1. **Painel OCI (VCN Security List)**:
   - Source: `0.0.0.0/0` | Protocolo: `UDP` | Porta: `19132`.
2. **Firewall Interno do Linux (`iptables`)**:
   ```bash
   sudo iptables -I INPUT 1 -p udp --dport 19132 -j ACCEPT
   sudo iptables -I INPUT 1 -p udp --dport 19133 -j ACCEPT
   sudo netfilter-persistent save
   ```
   *Verificar contagem de pacotes chegando:*
   ```bash
   sudo iptables -L INPUT -n -v | grep 19132
   ```
3. **Cloudflare DNS**:
   - Registro `A` apontando para o IP público da VM.
   - **Status do Proxy: DNS only (Cinza)**. O proxy laranja não encaminha tráfego UDP puro, bloqueando o handshake do jogo.

### Gotcha: RakNet vs NetherNet
- Se `transport=nethernet`: o servidor exige porta TCP aberta para handshake HTTP WebRTC antes de passar para UDP.
- Se a rede só tem UDP liberado: forçar no `server.properties`:
  ```properties
  transport=raknet
  server-port=19132
  server-portv6=19133
  server-ip=0.0.0.0
  ```

---

## ⛏️ 3. Operações do Minecraft Bedrock

### Instalação Limpa do Binário Oficial
```bash
URL="https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-1.26.52.3.zip"
curl -H "User-Agent: Mozilla/5.0" -L -o bedrock-server.zip "$URL"
unzip -q bedrock-server.zip -d ~/minecraft
chmod +x ~/minecraft/bedrock_server
```

### Gerenciamento de Jogadores & Operadores (OP)
- **Desativar Whitelist**:
  ```bash
  sed -i 's/^allow-list=.*/allow-list=false/' ~/minecraft/server.properties
  ```
- **Conceder OP via XUID**:
  Obtenha o XUID nos logs (`Player connected: <nick>, xuid: <xuid>`) e adicione em `~/minecraft/permissions.json`:
  ```json
  [
    {
      "permission": "operator",
      "xuid": "2535433945963160"
    }
  ]
  ```
  Reinicie o serviço: `sudo systemctl restart minecraft-bedrock`.

---

## 📋 4. Comandos de Diagnóstico Rápido

```bash
# Ver status e logs em tempo real
sudo systemctl status minecraft-bedrock
sudo journalctl -u minecraft-bedrock -f

# Checar porta aberta e processo escutando
sudo ss -tulpn | grep 19132

# Monitor de processos e memória
htop
```
