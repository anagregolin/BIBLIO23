from flask_bcrypt import generate_password_hash
def verifica_senha(senha):

    maiuscula = False
    minuscola = False
    pcd = False
    numero = False

    for itens in senha:
        if itens.upper():
            maiuscula = True
        if itens.lower():
            minuscola = True
        if itens.isdigit():
            numero = True
        if not itens.isalnum():
            pcd = True

    if maiuscula and minuscola and pcd and numero:
        return True
    else:
        return False


def criptografa(senha):
    return generate_password_hash(senha).decode('utf-8')