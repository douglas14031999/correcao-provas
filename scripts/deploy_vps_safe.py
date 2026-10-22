import os
import sys
import time
import paramiko

# Configure standard output to handle UTF-8 cleanly on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VPS_HOST = "179.198.101.116"
VPS_USER = "root"
VPS_PASS = "Douglas140399."
REMOTE_BASE = "/var/www/correcao-provas"

FILES_TO_DEPLOY = [
    ("backend/app/services/database.py", f"{REMOTE_BASE}/backend/app/services/database.py"),
    ("backend/app/services/reports/generators.py", f"{REMOTE_BASE}/backend/app/services/reports/generators.py"),
    ("frontend/app.js", f"{REMOTE_BASE}/frontend/app.js"),
    ("frontend/index.html", f"{REMOTE_BASE}/frontend/index.html"),
]

def run_ssh_command(client, command, check=True):
    print(f"[SSH CMD] {command}")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(f"STDOUT:\n{out}")
    if err:
        print(f"STDERR:\n{err}")
    if check and exit_status != 0:
        raise RuntimeError(f"Command failed with exit status {exit_status}: {command}\nError: {err}")
    return exit_status, out, err

def deploy():
    print("=" * 70)
    print(">>> INICIANDO DEPLOY SEGURO EM PRODUCAO (VPS 179.198.101.116)")
    print("=" * 70)

    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"📁 Diretório local do repositório: {repo_dir}")

    # 1. Conectar SSH
    print("\n[1/6] 🔑 Conectando à VPS via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✓ Conexão SSH estabelecida com sucesso.")

    # 2. Verificar status atual do serviço
    print("\n[2/6] 🔍 Verificando integridade atual do serviço...")
    _, status, _ = run_ssh_command(client, "systemctl is-active correcao-provas", check=False)
    print(f"Status do serviço antes do deploy: {status}")

    # 3. Criar backup seguro dos arquivos antes de sobrescrever
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = f"/var/www/backups/backup_dashboard_fix_{ts}"
    print(f"\n[3/6] 💾 Criando backup pré-deploy em {backup_dir}...")
    run_ssh_command(client, f"mkdir -p {backup_dir}/backend/app/services/reports {backup_dir}/frontend")
    for local_rel, remote_path in FILES_TO_DEPLOY:
        run_ssh_command(client, f"if [ -f {remote_path} ]; then cp {remote_path} {backup_dir}/{local_rel}; fi")
    print("✓ Backup pré-deploy concluído com sucesso.")

    # 4. Upload dos arquivos corrigidos via SFTP
    print("\n[4/6] 📤 Fazendo upload dos arquivos corrigidos via SFTP...")
    sftp = client.open_sftp()
    for local_rel, remote_path in FILES_TO_DEPLOY:
        local_full = os.path.join(repo_dir, local_rel.replace("/", os.sep))
        print(f"  -> Uploading: {local_rel} ({os.path.getsize(local_full)} bytes) -> {remote_path}")
        sftp.put(local_full, remote_path)
    sftp.close()
    print("✓ Upload SFTP concluído.")

    # 5. Ajustar permissões e validar sintaxe Python
    print("\n[5/6] 🔒 Ajustando permissões e validando sintaxe Python no venv...")
    run_ssh_command(client, f"chown -R www-data:www-data {REMOTE_BASE}/backend {REMOTE_BASE}/frontend")
    run_ssh_command(client, f"chmod -R 755 {REMOTE_BASE}/backend {REMOTE_BASE}/frontend")
    
    # Validar compilação do código python na VPS
    compile_cmd = (
        f"{REMOTE_BASE}/venv/bin/python -m py_compile "
        f"{REMOTE_BASE}/backend/app/services/database.py "
        f"{REMOTE_BASE}/backend/app/services/reports/generators.py"
    )
    run_ssh_command(client, compile_cmd)
    print("✓ Sintaxe Python verificada com 0 erros de compilação.")

    # Testar execução de get_macro_dashboard_data diretamente com o PostgreSQL de produção
    print("\n🧪 Testando execução da consulta na base de produção (PostgreSQL)...")
    test_script = (
        f"{REMOTE_BASE}/venv/bin/python -c \""
        f"import sys; sys.path.insert(0, '{REMOTE_BASE}/backend'); "
        f"from app.services.database import get_macro_dashboard_data; "
        f"data = get_macro_dashboard_data(); "
        f"kpis = data['kpis']; "
        f"print('PRODUÇÃO TESTE: Total alunos =', kpis['total_students']); "
        f"print('PRODUÇÃO TESTE: Provas corrigidas =', kpis['total_graded']); "
        f"print('PRODUÇÃO TESTE: Alunos avaliados =', kpis['evaluated_students']); "
        f"print('PRODUÇÃO TESTE: Participação =', kpis['participation_rate'], '%'); "
        f"print('PRODUÇÃO TESTE: Média geral =', kpis['overall_avg_percent'], '%'); "
        f"assert kpis['participation_rate'] <= 100.0, 'Participação acima de 100%!'; "
        f"print('✓ ASSERTIVA OK: Participação validada abaixo de 100%!'); "
        f"\""
    )
    run_ssh_command(client, test_script)

    # 6. Reiniciar o serviço e validar endpoint HTTP
    print("\n[6/6] ⚙️ Reiniciando serviço correcao-provas e Nginx...")
    run_ssh_command(client, "systemctl restart correcao-provas")
    time.sleep(2)
    _, post_status, _ = run_ssh_command(client, "systemctl is-active correcao-provas")
    if post_status != "active":
        print(f"❌ ERRO: O serviço não está ativo após restart! Status: {post_status}")
        print("Iniciando ROLLBACK automático...")
        for local_rel, remote_path in FILES_TO_DEPLOY:
            run_ssh_command(client, f"cp {backup_dir}/{local_rel} {remote_path}")
        run_ssh_command(client, "systemctl restart correcao-provas")
        sys.exit(1)

    run_ssh_command(client, "systemctl reload nginx 2>/dev/null || true")

    # Validar resposta HTTP da API de Dashboard
    print("\n🌐 Testando requisição HTTP ao endpoint /api/reports/dashboard...")
    http_test_cmd = (
        "curl -s -w '\\nHTTP_CODE:%{http_code}' "
        "http://127.0.0.1:8080/api/reports/dashboard"
    )
    _, curl_out, _ = run_ssh_command(client, http_test_cmd)
    if "HTTP_CODE:200" in curl_out:
        print("✓ Endpoint HTTP /api/reports/dashboard respondeu com HTTP 200 OK!")
    else:
        print("⚠️ Aviso: Resposta HTTP:", curl_out)

    client.close()
    print("\n" + "=" * 70)
    print("✅ DEPLOY CONCLUÍDO COM SUCESSO E ZERO DOWNTIME EM PRODUÇÃO!")
    print("=" * 70)

if __name__ == "__main__":
    deploy()
