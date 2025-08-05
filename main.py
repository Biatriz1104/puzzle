from pysat.solvers import Glucose4
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import time


N = None
NUM_PECAS = None
MAX_MOVIMENTOS = 100
direcoes = ['C', 'B', 'E', 'D']

# função responsavel por inicializar a configuração do tabuleiro , ou seja , 
#  definir o tamanho do tabuleiro e o estado final do puzzle , dependendo do numero fornecido pelo usuario.
def inicializar_configuracao(tamanho):
    global N, NUM_PECAS, estado_final
    N = tamanho
    NUM_PECAS = N * N
    
    cont = 0
    estado_final = []
    for i in range(N):
        lista = []
        for j in range(N):
            lista.append(cont)
            cont += 1
        estado_final.append(lista)

# dicionario de movimentos
movimentos = {
    "D": (0, 1),
    "E": (0, -1),
    "C": (-1, 0),
    "B": (1, 0),
}

# função que retorna lista de  posições válidas para cada movimento
def verifica_posicoes_validas(direcao):
    if direcao == "D":
        return [(i, j) for i in range(1, N + 1) for j in range(1, N)]
    elif direcao == "E":
        return [(i, j) for i in range(1, N + 1) for j in range(2, N + 1)]
    elif direcao == "C": 
        return [(i, j) for i in range(2, N + 1) for j in range(1, N + 1)]
    elif direcao == "B":
        return [(i, j) for i in range(1, N) for j in range(1, N + 1)]
    return []

# função que pega um tabuleiro resolvido e embaralha
#  com movimentos válidos 
def embaralhar_tabuleiro(tabuleiro_final, n=100):
    #cria uma copia do tabuleiro final , para não modificar o original
    tabuleiro = [linha[:] for linha in tabuleiro_final]
    # aqui guarda a posição do zero no tabuleiro
    i_zero, j_zero = None, None
    for i in range(N):
        for j in range(N):
            if tabuleiro[i][j] == 0:
                i_zero, j_zero = i, j
                break
        if i_zero is not None:
            break
    
    # embaralha o tabuleiro de uma forma q seja solucionavel
    for _ in range(n):
        # essa lista vai guardar os possiveis movimentos do zero
        moves = []
        if i_zero > 0: # se não está na primeira linha, pode mover para cima
            moves.append((i_zero - 1, j_zero))
        if i_zero < N - 1:# se não está na ultima linha, pode mover para baixo
            moves.append((i_zero + 1, j_zero))
        if j_zero > 0: # se não está na primeira coluna, pode mover para a esquerda
            moves.append((i_zero, j_zero - 1))
        if j_zero < N - 1: # se não está na ultima coluna, pode mover para a direita
            moves.append((i_zero, j_zero + 1))
        
        # se tem movimentos possíveis, escolhe um aleatório , e troca o zero com a peça da nova posição
        if moves:
            novo_i, novo_j = random.choice(moves) 
            tabuleiro[i_zero][j_zero], tabuleiro[novo_i][novo_j] = \
                tabuleiro[novo_i][novo_j], tabuleiro[i_zero][j_zero]
            i_zero, j_zero = novo_i, novo_j
    
    return tabuleiro

# essa função mapeia as variáveis do tabuleiro para um dicionário 
# e atribui um numero para que o solver entenda
def mapeamento(my_dict, cont, NUM_MOVIMENTOS):
    # mapeia variaveis das peças 
    for t in range(1, NUM_MOVIMENTOS + 2):
        for i in range(1, N + 1):
            for j in range(1, N + 1):
                for num in range(NUM_PECAS):
                    my_dict[f"{t}_P_{i}_{j}_{num}"] = cont
                    cont += 1 # contador certifica que cada variável tem um número único
    #mapeia variaveis das ações
    for t in range(1, NUM_MOVIMENTOS + 1):
        for valor in direcoes:
            my_dict[f"{t}_A_{valor}"] = cont
            cont += 1
    return my_dict

# essa função cria o modelo do puzzle,
# definindo as regras e restrições e retorna o solver e o dicionário de variáveis
def criar_modelo(NUM_MOVIMENTOS, estado_inicial):
    g = Glucose4()
    my_dict = {}
    cont = 1
    my_dict = mapeamento(my_dict, cont, NUM_MOVIMENTOS)

    #regra de restrição um , uma peça por posição
    for t in range(1, NUM_MOVIMENTOS + 2):
        for i in range(1, N + 1):
            for j in range(1, N + 1):
                g.add_clause([my_dict[f"{t}_P_{i}_{j}_{num}"] for num in range(NUM_PECAS)])
                #duas pecas nao podem ocupar a mesma posicao
                for num1 in range(NUM_PECAS):
                    for num2 in range(num1 + 1, NUM_PECAS):
                        peca1 = my_dict[f"{t}_P_{i}_{j}_{num1}"]
                        peca2 = my_dict[f"{t}_P_{i}_{j}_{num2}"]
                        g.add_clause([-peca1, -peca2])

    # regra de restrição 2 , cada peça em exatamente uma posição
    for t in range(1, NUM_MOVIMENTOS + 2):
        for num in range(NUM_PECAS):
            # Pelo menos uma posição para cada peça
            posicoes = [my_dict[f"{t}_P_{i}_{j}_{num}"] for i in range(1, N + 1) for j in range(1, N + 1)]
            g.add_clause(posicoes)
            # No máximo uma posição para cada peça
            for i in range(len(posicoes)):
                for j in range(i + 1, len(posicoes)):
                    g.add_clause([-posicoes[i], -posicoes[j]])

    #uma unica acao por passo (por tempo t)
    for t in range(1, NUM_MOVIMENTOS + 1):
        acoes = [my_dict[f"{t}_A_{d}"] for d in direcoes]
        g.add_clause(acoes)
        for i in range(len(acoes)):
            for j in range(i + 1, len(acoes)):
                g.add_clause([-acoes[i], -acoes[j]])

    #estado inicial
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            n = estado_inicial[i - 1][j - 1]
            g.add_clause([my_dict[f"1_P_{i}_{j}_{n}"]])

    #estado final
    passo_final = NUM_MOVIMENTOS + 1
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            n = estado_final[i - 1][j - 1]
            g.add_clause([my_dict[f"{passo_final}_P_{i}_{j}_{n}"]])

    #acoes validas (verifica se nao ta nas bordas do tabuleiro)
    for t in range(1, NUM_MOVIMENTOS + 1):
        for d in direcoes:
            a = my_dict[f"{t}_A_{d}"]
            validas = verifica_posicoes_validas(d)
            for i in range(1, N + 1):
                for j in range(1, N + 1):
                    if (i, j) not in validas:
                        g.add_clause([-a, -my_dict[f"{t}_P_{i}_{j}_0"]])

    #movimentacao
    for t in range(1, NUM_MOVIMENTOS + 1):
        for d, (di, dj) in movimentos.items():
            a = my_dict[f"{t}_A_{d}"]
            for i in range(1, N + 1):
                for j in range(1, N + 1):
                    ni, nj = i + di, j + dj
                    if not (1 <= ni <= N and 1 <= nj <= N):
                        continue
                    #pega posicao do 0 e da peca q ele vai trocar
                    for num in range(1, NUM_PECAS):
                        v0_t = my_dict[f"{t}_P_{i}_{j}_0"]
                        vn_t = my_dict[f"{t}_P_{ni}_{nj}_{num}"]
                        v0_tp1 = my_dict[f"{t+1}_P_{ni}_{nj}_0"]
                        vn_tp1 = my_dict[f"{t+1}_P_{i}_{j}_{num}"]
                        #adiciona nas clausulas pra realizar a troca 
                        g.add_clause([-a, -v0_t, -vn_t, v0_tp1])
                        g.add_clause([-a, -v0_t, -vn_t, vn_tp1])

    #regra de persistencia
    for t in range(1, NUM_MOVIMENTOS + 1):
        for d, (di, dj) in movimentos.items():
            a = my_dict[f"{t}_A_{d}"]
            for i in range(1, N + 1):
                for j in range(1, N + 1):
                    ni, nj = i + di, j + dj
                    #se for = a 0 ou a peca com a qual ele vai trocar então ignora
                    if not (1 <= ni <= N and 1 <= nj <= N):
                        continue
                    #para todas as outras posicoes aplica a regra
                    for ii in range(1, N + 1):
                        for jj in range(1, N + 1):
                            if (ii, jj) not in [(i, j), (ni, nj)]:
                                for num in range(NUM_PECAS):
                                    lit_t = my_dict[f"{t}_P_{ii}_{jj}_{num}"]
                                    lit_tp1 = my_dict[f"{t+1}_P_{ii}_{jj}_{num}"]
                                    g.add_clause([-a, -my_dict[f"{t}_P_{i}_{j}_0"], -lit_t, lit_tp1])

    return g, my_dict

#essa funcao imprime a solução do puzzle no terminal
# ela recebe o modelo que é a lista com as variaveis verdadeiras da solução 
# o dicionário de variáveis e o número de movimentos
def imprimir_solucao(modelo, my_dict, mov):
    # aqui cria um dicionário inverso para mapear os números de volta para os nomes das variáveis
    inv = {v: k for k, v in my_dict.items()}
    for t in range(1, mov + 2):#percorre por todos os passos e imprime
        print("Estado inicial" if t == 1 else f"Passo: {t - 1}")
        tabuleiro = [["" for _ in range(N)] for _ in range(N)]
        for var in modelo:
            if var > 0: # aqui garante que vai pegar as variaveis positivas
                nome = inv.get(var)#converte o numero da variavel de volta para string
                #verifica se é uma variável de peça e
                #  decompõe a string da variavel para pegar a posição e o número
                if nome and nome.startswith(f"{t}_P"):
                    partes = nome.split("_")
                    i = int(partes[2]) - 1
                    j = int(partes[3]) - 1
                    numero = partes[4]
                    tabuleiro[i][j] = numero
        #imprime o tabuleiro            
        for linha in tabuleiro:
            print(" ".join(linha))
        print()
        if t <= mov:
            for direcao in direcoes:
                nome_acao = f"{t}_A_{direcao}"
                if my_dict.get(nome_acao) in modelo:
                    print(f"Ação executada: {direcao}")
                    break

# função similar a imprimir_solucao, mas retorna dados em vez de imprimir no terminal
# ela retorna os tabuleiros e as ações executadas
def imprimir_interface(modelo, my_dict, mov):
    # dicionario inverso
    inv = {valor: chave for chave, valor in my_dict.items()}
    tabuleiros = [] 
    acoes = []     
    for t in range(1, mov + 2):#percorre por todos os passos
        tabuleiro = [[None for _ in range(N)] for _ in range(N)]
        for var in modelo:
            if var > 0:#decodifica as variaveis positivas
                nome_var = inv.get(var)
                if nome_var and nome_var.startswith(f"{t}_P"):
                    partes = nome_var.split("_") 
                    i = int(partes[2]) - 1
                    j = int(partes[3]) - 1
                    numero = int(partes[4])
                    tabuleiro[i][j] = numero
        tabuleiros.append(tabuleiro) #adiciona o tabuleiro completo na lista
        if t <= mov:# aqui coleta as ações e armazena na lista
            for direcao in direcoes:
                nome_acao = f"{t}_A_{direcao}"
                if my_dict.get(nome_acao) in modelo:
                    acoes.append(direcao)
                    break 

    return tabuleiros, acoes


#essa função vai criar a animação da transição usando a biblioteca matplotlib
# ela recebe os tabuleiros e as ações executadas
def animacao_movimento(boards, actions):
    # aqui cria a figura e o eixo para a animação
    fig, ax = plt.subplots()
    
    #limites do grafico
    ax.set_xlim(0, N)
    ax.set_ylim(0, N)
    ax.set_xticks(range(N + 1))
    ax.set_yticks(range(N + 1))
    ax.grid(True)
    ax.invert_yaxis()
    # cria um texto para cada posição do tabuleiro
    textos_do_tabuleiro = []
    for i in range(N):
        linha = []
        for j in range(N):
            texto = ax.text(
                j + 0.5,          
                i + 0.5,        
                "",               
                va="center",    
                ha="center",      
                fontsize=24    
            )
            linha.append(texto)
        textos_do_tabuleiro.append(linha)
    titulo = ax.set_title("8-puzzle")
    # essa função atualiza o quadro da animação
    # ela recebe o frame atual e atualiza os textos do tabuleiro
    def atualizar_quadro(frame):
        estado_atual = boards[frame]
        for i in range(N):
            for j in range(N):
                valor = estado_atual[i][j]
                textos_do_tabuleiro[i][j].set_text(str(valor))
        if frame == 0:
            titulo.set_text("Tabuleiro inicial")
        else:
            acao = actions[frame - 1]
            titulo.set_text(f"Passo {frame}: ação {acao}")

        elementos = []
        for linha in textos_do_tabuleiro:
            elementos.extend(linha)
        elementos.append(titulo)
        return elementos
    # cria a animação usando FuncAnimation
    animacao = animation.FuncAnimation(
        fig,
        atualizar_quadro,          
        frames=len(boards),         
        interval=800,             
        blit=False,                
        repeat=False
    )
    # exibe a animação
    plt.show()

#função principal
def main():
    # aqui define o limite de puzzle que o usuário pode escolher
    limite = [3,4,5,6]
    teste = True
    while teste:
        tamanho = int(input("Digite tamanho do puzzle: "))
        if tamanho in limite:
            inicializar_configuracao(tamanho)
            teste = False
            break
        else:
            print("Digite entre 3 e 6")
    # marca o tempo de início
    inicio = time.time()
    estado_inicial = embaralhar_tabuleiro(estado_final)
    for mov in range(0, MAX_MOVIMENTOS + 1):
        print(f"Testando com {mov} movimentos...")
        resultado = criar_modelo(mov, estado_inicial)
        if resultado[0] is None:
            print("Estado não solvível!")
            break
            
        g, my_dict = resultado
        # aqui tenta resolver o puzzle
        if g.solve():
            fim = time.time()
            print(f"\nSolução encontrada com {mov} movimentos!")
            modelo = g.get_model()
            imprimir_solucao(modelo, my_dict, mov)
            print(f"\nencontrado em {fim - inicio:.2f} segundos")
            boards, actions = imprimir_interface(modelo, my_dict, mov)
            animacao_movimento(boards, actions)
            break
    else:
        print(f"Nenhuma solução encontrada com até {MAX_MOVIMENTOS} movimentos!")


if __name__ == "__main__":
    main()