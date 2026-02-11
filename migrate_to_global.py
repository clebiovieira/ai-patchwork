#!/usr/bin/env python3
import os
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path

def setup_args():
    parser = argparse.ArgumentParser(description="Migrate .agent workspace configs to global Antigravity home.")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without performing them.")
    parser.add_argument("--src", type=str, default=".agent", help="Source .agent directory.")
    parser.add_argument("--dest", type=str, default=str(Path.home() / ".gemini" / "antigravity"), help="Destination global directory.")
    parser.add_argument("--backup-dir", type=str, default=str(Path.home() / ".gemini" / "antigravity_backups"), help="Directory for backups.")
    return parser.parse_args()

def log(msg, dry_run=False):
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"{prefix}{msg}")

def backup_global(dest_path, backup_dir, dry_run=False):
    if not os.path.exists(dest_path):
        log(f"Destination {dest_path} does not exist. Skipping backup.", dry_run)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"antigravity_backup_{timestamp}")
    
    log(f"Creating backup of {dest_path} at {backup_path}", dry_run)
    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copytree(dest_path, backup_path)

def merge_mcp_configs(src_dir, dest_dir, dry_run=False):
    src_config_path = os.path.join(src_dir, "mcp_config.json")
    dest_config_path = os.path.join(dest_dir, "mcp_config.json")

    if not os.path.exists(src_config_path):
        log("No mcp_config.json found in source. Skipping merge.")
        return

    if not os.path.exists(dest_config_path):
        log(f"No global mcp_config.json found. Copying from {src_config_path}", dry_run)
        if not dry_run:
            shutil.copy2(src_config_path, dest_config_path)
        return

    log(f"Merging {src_config_path} into {dest_config_path}", dry_run)
    if not dry_run:
        with open(src_config_path, 'r') as f:
            src_config = json.load(f)
        with open(dest_config_path, 'r') as f:
            dest_config = json.load(f)

        # Merge 'mcpServers' section
        src_servers = src_config.get("mcpServers", {})
        dest_servers = dest_config.get("mcpServers", {})
        
        for server_name, server_config in src_servers.items():
            if server_name in dest_servers:
                log(f"  Conflict: Overwriting global config for server '{server_name}'")
            dest_servers[server_name] = server_config

        dest_config["mcpServers"] = dest_servers
        
        with open(dest_config_path, 'w') as f:
            json.dump(dest_config, f, indent=2)

def migrate_directories(src_dir, dest_dir, dry_run=False):
    # Mapping source subdir to destination subdir
    mapping = {
        "agents": "agents",
        "skills": "skills",
        "workflows": "global_workflows",
        "rules": "rules",
        "scripts": "scripts"
    }

    for src_sub, dest_sub in mapping.items():
        src_path = os.path.join(src_dir, src_sub)
        dest_path = os.path.join(dest_dir, dest_sub)

        if not os.path.exists(src_path):
            continue

        log(f"Migrating {src_path} -> {dest_path}", dry_run)
        if not dry_run:
            os.makedirs(dest_path, exist_ok=True)
            for item in os.listdir(src_path):
                s = os.path.join(src_path, item)
                d = os.path.join(dest_path, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

def main():
    args = setup_args()
    log(f"Starting migration from {args.src} to {args.dest}")
    
    # 1. Backup
    backup_global(args.dest, args.backup_dir, args.dry_run)
    
    # Ensure destination exists
    if not args.dry_run:
        os.makedirs(args.dest, exist_ok=True)

    # 2. Migrate Directories
    migrate_directories(args.src, args.dest, args.dry_run)
    
    # 3. Merge MCP Config
    merge_mcp_configs(args.src, args.dest, args.dry_run)
    
    log("\n" + "="*60)
    log("⚠️  IMPORTANT NOTE ON RULES:")
    log("The directory 'rules/' has been migrated to your global Antigravity folder.")
    log("However, for global effects, the system primarily reads '~/.gemini/GEMINI.md'.")
    log("To make these rules active globally, you must manually merge or copy")
    log("the contents from 'antigravity/rules/GEMINI.md' to '~/.gemini/GEMINI.md'.")
    log("="*60 + "\n")

    log("Migration completed successfully!")

if __name__ == "__main__":
    main()
