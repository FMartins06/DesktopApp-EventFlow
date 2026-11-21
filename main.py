"""Inicializa o EventFlow desktop ou as interfaces anteriores."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="EventFlow - gerenciamento de eventos")
    opcoes = parser.add_mutually_exclusive_group()
    opcoes.add_argument("--terminal", action="store_true", help="abrir o menu de terminal")
    opcoes.add_argument("--tk", action="store_true", help="abrir a interface gráfica anterior")
    args = parser.parse_args()
    if args.terminal:
        from aplicacao import MenuEventFlow
        MenuEventFlow().executar()
    elif args.tk:
        from interface_grafica import InterfaceEventFlow
        InterfaceEventFlow().executar()
    else:
        from interface_web import executar
        executar()


if __name__ == "__main__":
    main()

