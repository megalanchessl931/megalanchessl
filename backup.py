#!/usr/bin/env python3
"""
Script de backup automático para aplicação Flask.
Gera backups compactados do banco de dados, códigos, templates e configurações.

Uso:
    python backup.py              # Menu interativo
    python backup.py create       # Cria backup direto
    python backup.py list         # Lista backups
    python backup.py restore NOME # Restaura backup específico
"""

import os
import shutil
import zipfile
import sys
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÕES - AJUSTE CONFORME NECESSÁRIO
# ═══════════════════════════════════════════════════════════

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

# Diretórios para backup (excluindo venv, __pycache__, etc.)
DIRECTORIES_TO_BACKUP = [
    "app",
    "migrations",
    "data",
    "tests",    
]

# Arquivos importantes da raiz
FILES_TO_BACKUP = [
#    ".env",
    ".env.example",
    "requirements.txt",
    "run.py",
    "README.md",
    "start.sh",
]

# Banco de dados (ajuste conforme seu setup)
DATABASE_PATHS = [
    Path("instance/app.db"),
    Path("app.db"),
    Path("data/app.db"),
]

# Padrões para excluir durante o backup (similar ao seu tree -I)
EXCLUDE_PATTERNS = [
    "venv",
    "__pycache__",
    "*.pyc",
    ".git",
    "instance",  # banco já é copiado separadamente
    "flask_session",
    ".pytest_cache",
    ".mypy_cache",
    "backups",
    "*.zip",
    "*.log",
]


# ═══════════════════════════════════════════════════════════
# FUNÇÕES DE BACKUP
# ═══════════════════════════════════════════════════════════

def get_timestamp():
    """Retorna timestamp formatado para nome do arquivo."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def should_exclude(path: Path) -> bool:
    """Verifica se o caminho deve ser excluído do backup."""
    path_str = str(path)
    name = path.name
    
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        else:
            if pattern in path_str:
                return True
    
    return False


def backup_database(backup_path: Path):
    """Faz backup dos bancos de dados SQLite encontrados."""
    db_dir = backup_path / "database"
    db_dir.mkdir(exist_ok=True)
    
    found = False
    for db_path in DATABASE_PATHS:
        if db_path.exists():
            dest = db_dir / f"{db_path.stem}_{get_timestamp()}.db"
            shutil.copy2(db_path, dest)
            print(f"✓ Banco copiado: {db_path} → {dest}")
            found = True
    
    if not found:
        print("⚠ Nenhum banco de dados encontrado")


def backup_directories(backup_path: Path):
    """Faz backup dos diretórios do projeto, excluindo padrões desnecessários."""
    for dir_path in DIRECTORIES_TO_BACKUP:
        source = Path(dir_path)
        if not source.exists():
            print(f"⚠ Diretório não encontrado: {dir_path}")
            continue
        
        dest = backup_path / source.name
        dest.mkdir(exist_ok=True)
        
        copied = 0
        skipped = 0
        
        for item in source.rglob("*"):
            if item.is_file() and not should_exclude(item):
                rel_path = item.relative_to(source)
                dest_file = dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                copied += 1
            elif item.is_file():
                skipped += 1
        
        print(f"✓ Diretório: {dir_path} ({copied} arquivos, {skipped} excluídos)")


def backup_files(backup_path: Path):
    """Faz backup dos arquivos de configuração da raiz."""
    files_dir = backup_path / "root_files"
    files_dir.mkdir(exist_ok=True)
    
    for file_path in FILES_TO_BACKUP:
        source = Path(file_path)
        if source.exists():
            shutil.copy2(source, files_dir / source.name)
            print(f"✓ Arquivo: {file_path}")
        else:
            print(f"⚠ Arquivo não encontrado: {file_path}")


def create_zip_backup(timestamp: str = None):
    """Cria um arquivo ZIP com todo o backup."""
    if timestamp is None:
        timestamp = get_timestamp()
    
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir(exist_ok=True)
    
    print(f"\n📦 Criando backup: backup_{timestamp}")
    print("=" * 60)
    
    # Executa os backups
    backup_database(backup_path)
    backup_directories(backup_path)
    backup_files(backup_path)
    
    # Cria o ZIP compactado
    zip_filename = BACKUP_DIR / f"backup_{timestamp}.zip"
    total_files = 0
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(backup_path.parent)
                zipf.write(file_path, arcname)
                total_files += 1
    
    # Remove a pasta temporária
    shutil.rmtree(backup_path)
    
    size_mb = zip_filename.stat().st_size / 1024 / 1024
    print(f"\n✅ Backup criado: {zip_filename.name}")
    print(f"📊 {total_files} arquivos | {size_mb:.2f} MB")
    
    return zip_filename


def list_backups():
    """Lista todos os backups existentes."""
    backups = sorted(BACKUP_DIR.glob("backup_*.zip"))
    
    if not backups:
        print("\n📭 Nenhum backup encontrado em", BACKUP_DIR.absolute())
        return
    
    print(f"\n📋 Backups ({len(backups)} encontrados):")
    print("=" * 70)
    print(f"{'#':<3} {'Nome do arquivo':<40} {'Tamanho':<12} {'Data':<20}")
    print("-" * 70)
    
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        date_str = mtime.strftime("%Y-%m-%d %H:%M")
        print(f"{i:<3} {backup.name:<40} {size_mb:>8.2f} MB   {date_str}")


def restore_backup(backup_name: str):
    """Restaura um backup específico."""
    backup_path = BACKUP_DIR / backup_name
    
    if not backup_path.exists():
        if not backup_path.suffix:
            backup_path = BACKUP_DIR / f"{backup_name}.zip"
    
    if not backup_path.exists():
        print(f"\n❌ Backup não encontrado: {backup_name}")
        list_backups()
        return
    
    print(f"\n🔄 Restaurando: {backup_path.name}")
    print("=" * 60)
    
    confirm = input("⚠️  Isso sobrescreverá arquivos existentes. Continuar? (s/N): ")
    if confirm.lower() != 's':
        print("❌ Restauração cancelada")
        return
    
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(".")
    
    print("\n✅ Backup restaurado com sucesso!")
    print("⚠️  Verifique se o banco de dados e as configurações estão corretos.")


def cleanup_old_backups(days: int = 30):
    """Remove backups mais antigos que X dias."""
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    removed = 0
    
    print(f"\n🧹 Limpando backups com mais de {days} dias...")
    print("=" * 60)
    
    for backup in BACKUP_DIR.glob("backup_*.zip"):
        if backup.stat().st_mtime < cutoff:
            size_mb = backup.stat().st_size / 1024 / 1024
            print(f"🗑️  {backup.name} ({size_mb:.2f} MB)")
            backup.unlink()
            removed += 1
    
    if removed == 0:
        print("Nenhum backup antigo encontrado.")
    else:
        print(f"\n✅ {removed} backup(s) removido(s).")


def show_help():
    """Mostra ajuda de uso."""
    help_text = """
🔐 Backup Automático - Aplicação Flask

Uso:
    python backup.py              # Menu interativo
    python backup.py create       # Cria backup imediatamente
    python backup.py list         # Lista todos os backups
    python backup.py restore NOME # Restaura backup específico
    python backup.py cleanup [DIA] # Remove backups antigos (default: 30 dias)
    python backup.py help         # Mostra esta ajuda

Exemplos:
    python backup.py create
    python backup.py restore backup_20260803_143022.zip
    python backup.py cleanup 7
"""
    print(help_text)


def main():
    """Função principal."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_zip_backup()
        elif command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleanup_old_backups(days)
        elif command == "help":
            show_help()
        else:
            print(f"❌ Comando desconhecido: {command}")
            show_help()
        return
    
    # Menu interativo
    print("🔐 Sistema de Backup - Aplicação Flask")
    print("=" * 60)
    print(f"📁 Pasta de backups: {BACKUP_DIR.absolute()}")
    
    while True:
        print("\n" + "=" * 60)
        print("1. 📦 Criar backup completo")
        print("2. 📋 Listar backups")
        print("3. 🔄 Restaurar backup")
        print("4. 🧹 Limpar backups antigos (>30 dias)")
        print("5. ❌ Sair")
        
        choice = input("\nEscolha (1-5): ").strip()
        
        if choice == "1":
            create_zip_backup()
        elif choice == "2":
            list_backups()
        elif choice == "3":
            list_backups()
            name = input("\nNome ou número do backup: ").strip()
            if name.isdigit():
                backups = sorted(BACKUP_DIR.glob("backup_*.zip"))
                if 1 <= int(name) <= len(backups):
                    restore_backup(backups[int(name) - 1].name)
                else:
                    print("❌ Número inválido")
            elif name:
                restore_backup(name)
        elif choice == "4":
            cleanup_old_backups()
        elif choice == "5":
            print("\n👋 Saindo...")
            break
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    main()
