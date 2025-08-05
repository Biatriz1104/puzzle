import multiprocessing
import time
from main import (criar_modelo, imprimir_interface, animacao_movimento, 
                  imprimir_solucao, MAX_MOVIMENTOS, embaralhar_tabuleiro, 
                  inicializar_configuracao)

def tentar_movimentos(mov, estado_inicial, tamanho, queue):

    inicializar_configuracao(tamanho)
    
    if not queue.empty():
        return
    
    resultado = criar_modelo(mov, estado_inicial)
    if resultado[0] is None:
        return None
    
    g, my_dict = resultado
    if g.solve():
        modelo = g.get_model()
        boards, actions = imprimir_interface(modelo, my_dict, mov)
        if queue.empty():
            queue.put((mov, boards, actions, modelo, my_dict))

def main():
    tamanho = int(input("Digite tamanho do puzzle: "))
    inicializar_configuracao(tamanho)
    
    from main import estado_final
    
    estado_inicial = embaralhar_tabuleiro(estado_final)

    print("Tentando resolver o tabuleiro embaralhado com múltiplos processos...")
    
    inicio = time.time()

    with multiprocessing.Manager() as manager:
        queue = manager.Queue()
        with multiprocessing.Pool() as pool:
            processos = []
            for mov in range(MAX_MOVIMENTOS + 1):
                processo = pool.apply_async(tentar_movimentos, (mov, estado_inicial, tamanho, queue))
                processos.append(processo)

            resultado = None
            while queue.empty() and any(not p.ready() for p in processos):
                time.sleep(0.1)
            
            # Se a queue não está vazia, pega a solução
            if not queue.empty():
                resultado = queue.get()

            # Encerra os demais processos
            pool.terminate()
            pool.join()

    fim = time.time()

    if resultado:
        mov, boards, actions, modelo, my_dict = resultado
        imprimir_solucao(modelo, my_dict, mov)
        print(f"\nSolução encontrada com {mov} movimentos!")
        print(f"Tempo total: {fim - inicio:.2f} segundos\n")
        animacao_movimento(boards, actions)
    else:
        print(f"\nNenhuma solução encontrada com até {MAX_MOVIMENTOS} movimentos.")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")  # Necessário no Windows
    main()