# /desktop - AIOS Desktop App Launcher

Inicia o AIOS Desktop (Electron + Dashboard).

## Execucao

Execute os seguintes passos:

1. **Verificar branch**: Confirme que esta no branch `feat/desktop-electron-app`
2. **Matar processos antigos**: Encerre processos Electron anteriores
3. **Verificar Dashboard**: Se nao estiver rodando na porta 3000, inicie-o
4. **Build Electron**: Compile o TypeScript se necessario
5. **Iniciar Electron**: Execute o app desktop

## Comandos

```bash
# Verificar/trocar branch
git checkout feat/desktop-electron-app

# Matar Electron antigo
powershell -NoProfile -Command "Get-Process electron -ErrorAction SilentlyContinue | Stop-Process -Force"

# Verificar porta 3000
netstat -ano | grep ":3000"

# Se porta livre, iniciar dashboard
cd apps/dashboard && npm run dev &

# Aguardar dashboard
sleep 5

# Iniciar Electron
cd apps/desktop && npm run build && node start-electron.js
```

## Resultado Esperado

- Dashboard rodando em http://localhost:3000
- Janela Electron do AIOS Desktop aberta
- System tray com icone do AIOS
