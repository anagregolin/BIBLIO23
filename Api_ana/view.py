from flask import jsonify, request, send_file
from main import app, con
from funcao import verifica_senha, criptografa
from flask_bcrypt import  check_password_hash
from fpdf import FPDF
import os

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/livro', methods=['GET'])
def livro():
    try:
        cur = con.cursor()
        cur.execute("select id_livros, nome, autor, ano_publicacao FROM livros")
        livros = cur.fetchall()
        livros_list = []
        for livros in livros:
            livros_list.append({
                'id_livros':livros[0],
                'nome':livros[1],
                'autor':livros[2],
                'ano_publicacao':livros[3]
            })
        return jsonify(mensagem='lista de livros', livros=livros_list)

    except Exception as e:
        return jsonify(mensagem=f"Erro ao consultar banco de dados: {e}"), 500
    finally:
        cur.close()


@app.route('/criar_livros', methods=['POST'])
def criar_livros():

    try:

        nome = request.form.get('nome')
        autor = request.form.get('autor')
        ano_publicacao = request.form.get('ano_publicacao')
        imagem = request.files.get('imagem')


        cur = con.cursor()
        cur.execute("select 1 from livros where nome = ?", (nome,))
        if cur.fetchone():
            return jsonify({"error": "Livro já cadastrado"}), 400
        cur.execute("""INSERT INTO livros (nome, autor, ano_publicacao)
                   VALUES (?, ?, ?) RETURNING id_livros""", (nome, autor, ano_publicacao))

        codigo_livro = cur.fetchone()[0]
        con.commit()

        caminho_imagem = None

        if imagem:
            nome_imagem = f"{codigo_livro}.jpg"
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Livros")
            os.makedirs(caminho_imagem_destino, exist_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)

        return jsonify({
            'message': "Livro cadastrado com sucesso",
            'livros': {
                'nome': nome,
                'autor': autor,
                'ano_publicacao': ano_publicacao
                }
                }),201
    except Exception as e:
        return jsonify(mensagem=f"Erro ao cadastrar livro: {e}"), 500
    finally:
        cur.close()

@app.route('/editar_livro/<int:id>', methods=['PUT'])
def editar_livro(id):
    cur = con.cursor()
    cur.execute("""SELECT ID_LIVROS, NOME, AUTOR, ANO_PUBLICACAO 
                         FROM LIVROS 
                        WHERE ID_LIVROS = ?""", (id,))
    tem_livro = cur.fetchone()
    if not tem_livro:
            cur.close()
            return jsonify({"error": "Livro não encontrado"}), 404

    data = request.get_json()
    nome = data.get('nome')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cur.execute("""UPDATE LIVROS SET NOME = ?, AUTOR = ?, ANO_PUBLICACAO = ?
                    WHERE ID_LIVROS = ?""", (nome, autor, ano_publicacao, id))
    con.commit()
    cur.close()

    return jsonify({"message": "Livro atualizado com sucesso",
                        'livro':
                            {
                            'id_livros': id,
                            'nome': nome,
                            'autor': autor,
                            'ano_publicacao': ano_publicacao
                             }
                        })


@app.route ('/deletar_livro/<int:id>', methods=['DELETE'])
def deletar_livro(id):
        cur = con.cursor()
        cur.execute("SELECT 1 FROM livros WHERE id_livros = ?", (id,))
        if not cur.fetchone():
            return jsonify({"error": "Livro não encontrado"}), 404
        cur.execute("DELETE FROM livros WHERE id_livros = ?", (id,))
        con.commit()
        return jsonify({"message": "Livro deletado com sucesso"})


@app.route('/usuarios', methods=['GET'])
def usuarios():
    try:
        cur = con.cursor()
        cur.execute("select id_usuarios, nome, usuario, senha FROM usuarios")
        usuarios = cur.fetchall()

        lista_usuarios = []

        for usuarios in usuarios:
            lista_usuarios.append({
                'id_usuarios':usuarios[0],
                'nome':usuarios[1],
                'usuario':usuarios[2],
                'senha':usuarios[3],
                   })
        return jsonify(mensagem='lista de pessoas', abacate=lista_usuarios)
    except Exception as e:
        return jsonify(mensagem=f"Erro ao consultar banco de dados: {e}"), 500
    finally:
        cur.close()

@app.route('/criar_usuarios', methods=['POST'])
def criar_usuarios():

    data = request.get_json()

    nome = data.get('nome')
    usuario = data.get('usuario')
    senha = data.get('senha')

    try:
        cur = con.cursor()
        cur.execute("select 1 from usuarios where nome = ?", (nome,))
        if cur.fetchone():
            return jsonify({"error": "Usuário já cadastrado"}), 400



        if verifica_senha(senha):
            senha_criptografada = criptografa(senha)
            cur.execute("""INSERT INTO usuarios (nome, usuario, senha)
                   VALUES (?, ?, ?)""", (nome, usuario, senha_criptografada))
            con.commit()
            return jsonify({
                'message': "Usuário cadastrado com sucesso",
                'livros': {
                'nome': nome,
                'usuario':usuario,
                'senha': senha
                }
                    }),201
        else:
            return jsonify(message="Senha Fraca")

    except Exception as e:
        return jsonify(mensagem=f"Erro ao cadastrar usuário: {e}"), 500
    finally:
        cur.close()

@app.route('/deletar_usuarios/<int:id_usuarios>', methods=['DELETE'])
def deletar_usuarios(id_usuarios):
        cursor = con.cursor()
        try:
            cursor.execute('DELETE FROM usuarios WHERE id_usuarios = ?', (id_usuarios,))
            con.commit()
            return jsonify(mesagem="Usuario deletado com sucesso")

        except Exception:
            con.rollback()
            return jsonify(message='Erro ao excluir o usuário.')
        finally:
            cursor.close()


@app.route('/editar_usuarios/<int:id_usuarios>', methods=['PUT'])
def editar_usuarios(id_usuarios):

    try:
        cur = con.cursor()
        cur.execute("""SELECT ID_USUARIOS, NOME FROM USUARIOS 
                            WHERE ID_USUARIOS = ?""", (id_usuarios,))
        tem_usuario = cur.fetchone()
        if not tem_usuario:

                return jsonify({"error": "Usuário não encontrado"}), 404

        data = request.get_json()
        nome = data.get('nome')
        usuario = data.get('usuario')
        senha = data.get('senha')

        if verifica_senha(senha):
            senha_criptografada = criptografa(senha)
            cur.execute("""UPDATE USUARIOS SET NOME = ?, USUARIO = ?, SENHA = ?
                                    WHERE ID_USUARIOS = ?""", (nome, usuario, senha_criptografada, id_usuarios))
            con.commit()
            return jsonify({
                'message': "Usuário editado com sucesso",
                'livros': {
                    'nome': nome,
                    'usuario': usuario,
                    'senha': senha
                }
            }), 201
        else:
            return jsonify(message="Senha Fraca")

    except Exception as e:
        con.rollback()
        return jsonify({"message":f"Erro ao excluir o usuário.{e}"})
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        usuario = data.get('usuario')
        senha = data.get('senha')

        cur = con.cursor()
        cur.execute("""SELECT ID_USUARIOS, NOME, USUARIO, SENHA FROM USUARIOS 
                                    WHERE USUARIO = ?""", (usuario,))
        tem_usuario = cur.fetchone()
        if not tem_usuario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        senha_hash= tem_usuario[3]

        if check_password_hash(senha_hash, senha):
            return jsonify({
                'message': "Usuário logado com sucesso",
                'usuario': {
                    'id_usuario': tem_usuario[0],
                    'nome': tem_usuario[1],
                    'usuario': tem_usuario[2],
                    'senha': tem_usuario[3]
                }
            }), 201
        else:
            return jsonify(message="Senha Incorreta")
    except Exception as e:
        return jsonify(mensagem = f'Erro ao consultar o banco de dados: {e}'), 500
    finally:
        cur.close()


@app.route('/relatorio_usuario', methods=['GET'])
def relatorio_usuario():
    try:
        cur = con.cursor()
        cur.execute("""SELECT ID_USUARIOS, NOME, USUARIO FROM USUARIOS""")
        usuarios = cur.fetchall()
        qtd_usuarios = len(usuarios)

        pdf = FPDF()
        pdf.set_auto_page_break(auto= True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, "Relatório de usuários cadastrados", ln=True, align='C')
        pdf.ln(3)

        pdf.set_font("Arial", size=12)
        if not usuarios:
            pdf.cell(200, 10, "Nenhum usuário encontrado", ln=True, align='C')
        else:
            for usuario in usuarios:
                pdf.cell(200, 10, f"ID: {usuario[0]} - Nome: {usuario[1]} - Usuário: {usuario[2]}", ln=True)

            pdf.ln(5)
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(200, 10, f"Total de usuários cadastrados: {qtd_usuarios}", ln= True)

        pdf_path = "relatorio_usuario.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return jsonify(mensagem=f'Erro ao gerar relatório: {e}'), 500

    finally:
        cur.close()



@app.route('/relatorio_livros', methods=['GET'])
def relatorio_livros():
    try:
        cur = con.cursor()
        cur.execute("""SELECT ID_LIVROS, NOME, AUTOR, ANO_PUBLICACAO FROM USUARIOS""")
        livros = cur.fetchall()
        qtd_livros = len(livros)

        pdf = FPDF()
        pdf.set_auto_page_break(auto= True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, "Relatório de livros cadastrados", ln=True, align='C')
        pdf.ln(3)

        pdf.set_font("Arial", size=12)
        if not usuarios:
            pdf.cell(200, 10, "Nenhum livro encontrado", ln=True, align='C')
        else:
            for livro in livros:
                pdf.cell(200, 10, f"ID: {livros[0]} - Nome: {livros[1]} - Autor: {livros[2]} - Ano de Publicacao:{livros[3]}", ln=True)

            pdf.ln(5)
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(200, 10, f"Total de livros cadastrados: {qtd_usuarios}", ln= True)

        pdf_path = "relatorio_usuario.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return jsonify(mensagem=f'Erro ao gerar relatório: {e}'), 500

    finally:
        cur.close()

