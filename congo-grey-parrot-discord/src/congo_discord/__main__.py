import sys

if len(sys.argv) > 1 and sys.argv[1] == "conector":
    from congo_discord.presentation.bot import connector_report

    if "--conectar" in sys.argv or "--desconectar" in sys.argv:
        connector_report()  # põe a pasta mcp do projeto no sys.path
        import conector

        print(conector.connect("congo-discord") if "--conectar" in sys.argv else conector.disconnect("congo-discord"))
    else:
        print(connector_report())
    raise SystemExit(0)

from congo_discord.presentation.bot import main  # noqa: E402

if __name__ == "__main__":
    main()
