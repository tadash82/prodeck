"""Ponto de entrada para o PyInstaller (o pacote usa imports relativos, então
não dá para apontar o PyInstaller direto para main.py)."""

from prodeck_agent.main import main

if __name__ == "__main__":
    main()
