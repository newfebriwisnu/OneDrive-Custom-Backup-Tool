#!/usr/bin/env python3
"""
OneDrive Custom Backup Folder Tool
Main application entry point with CLI/GUI detection
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from gui.main_window import MainWindow
from core.backup import BackupManager
from utils.logging import setup_logging
from utils.config import AppConfig


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="OneDrive Custom Backup Folder Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --source "C:\\MyFolder" --target "C:\\Users\\Username\\OneDrive\\Backup\\MyFolder"
  python main.py --source "C:\\MyFolder" --target "C:\\Users\\Username\\OneDrive\\Backup\\MyFolder" --silent
  python main.py --validate-only --source "C:\\MyFolder" --target "C:\\Users\\Username\\OneDrive\\Backup\\MyFolder"
        """
    )

    parser.add_argument('--source',
                        help='Source folder path to backup')
    parser.add_argument('--target',
                        help='Target OneDrive path')
    parser.add_argument('--silent',
                        action='store_true',
                        help='Run without GUI')
    parser.add_argument('--validate-only',
                        action='store_true',
                        help='Validate paths only')
    parser.add_argument('--verbose',
                        action='store_true',
                        help='Detailed output')
    parser.add_argument('--list-junctions',
                        action='store_true',
                        help='List all junction links')

    try:
        return parser.parse_args()
    except SystemExit:
        # Handle help and error cases for windowed applications
        if len(sys.argv) == 1:
            # No arguments, return None to trigger GUI mode
            return None
        else:
            # Re-raise for actual errors
            raise


def run_cli_mode(args):
    """Run in command line mode"""
    logger = setup_logging(verbose=args.verbose)
    backup_manager = BackupManager()

    # Handle list-junctions option
    if args.list_junctions:
        from core.junction_manager import JunctionManager
        junction_manager = JunctionManager()

        print("Searching for junction links...")
        junctions = junction_manager.list_junctions()

        if not junctions:
            print("No junction links found")
            return True

        print(f"Found {len(junctions)} junction link(s):")
        print("-" * 80)

        for i, junction in enumerate(junctions, 1):
            source = junction.get('source', 'Unknown')
            target = junction.get('target', 'Unknown')
            created = junction.get('created', 'Unknown')

            print(f"{i:2d}. {source}")
            print(f"    → {target}")
            print(f"    Created: {created}")
            print()

        return True

    if not args.source or not args.target:
        print("Error: Both --source and --target are required for CLI mode")
        return False

    try:
        # Validate paths
        is_valid, error_msg = backup_manager.validate_paths(
            args.source, args.target)
        if not is_valid:
            print(f"Validation Error: {error_msg}")
            return False

        if args.validate_only:
            print("✓ Paths validation successful")
            return True

        # Execute backup
        if not args.silent:
            print(f"Moving '{args.source}' to '{args.target}'...")

        success = backup_manager.execute_backup(args.source, args.target)

        if success:
            if not args.silent:
                print("✓ Backup completed successfully")
            return True
        else:
            print("✗ Backup failed")
            return False

    except Exception as e:
        import traceback
        logger.error(f"CLI execution error: {e}", exc_info=True)
        print(f"Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def run_gui_mode():
    """Run in GUI mode"""
    try:
        setup_logging()
        app = MainWindow()
        app.run()
        return True
    except Exception as e:
        # For console debugging, print full traceback
        import traceback
        error_msg = f"GUI Error: {e}"
        print(error_msg)
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Also log the error
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"GUI startup failed: {e}", exc_info=True)
        except:
            pass  # If logging fails, at least we printed to console
            
        return False


def main():
    """Main application entry point"""
    try:
        args = parse_arguments()

        # If args is None, it means no arguments were provided or help was requested
        if args is None:
            # Default to GUI mode
            success = run_gui_mode()
            sys.exit(0 if success else 1)

        # Determine mode based on arguments
        if args.source or args.target or args.silent or args.validate_only or args.list_junctions:
            # CLI mode
            success = run_cli_mode(args)
            sys.exit(0 if success else 1)
        else:
            # GUI mode
            success = run_gui_mode()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        import traceback
        print(f"Fatal Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Try to log the error if possible
        try:
            setup_logging()
            import logging
            logger = logging.getLogger(__name__)
            logger.critical(f"Application startup failed: {e}", exc_info=True)
        except:
            pass  # If logging fails, at least we printed to console
            
        sys.exit(1)


if __name__ == "__main__":
    main()
