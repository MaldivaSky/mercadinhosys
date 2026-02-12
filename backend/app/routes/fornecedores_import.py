

@fornecedores_bp.route("/import", methods=["POST"])
@funcionario_required
def importar_fornecedores():
    """Importa fornecedores via arquivo CSV ou Excel"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400

        try:
            items = read_import_file(file)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
            
        criados = 0
        atualizados = 0
        erros = []
        
        for index, item in enumerate(items):
            try:
                # Validação mínima
                nome = item.get('nome_fantasia') or item.get('nome')
                if not nome:
                    erros.append(f"Linha {index+1}: Nome Fantasia é obrigatório")
                    continue
                
                # Normaliza dados
                cnpj = str(item.get('cnpj', '')).strip()
                cnpj_limpo = re.sub(r'\D', '', cnpj)
                
                # Procura existente
                fornecedor = None
                if cnpj_limpo:
                    fornecedor = Fornecedor.query.filter_by(
                        estabelecimento_id=estabelecimento_id,
                        cnpj=formatar_cnpj(cnpj_limpo)
                    ).first()
                
                if not fornecedor:
                    fornecedor = Fornecedor.query.filter_by(
                        estabelecimento_id=estabelecimento_id,
                        nome_fantasia=nome
                    ).first()

                if fornecedor:
                    # Atualizar
                    fornecedor.razao_social = item.get('razao_social', fornecedor.razao_social)
                    fornecedor.email = item.get('email', fornecedor.email)
                    fornecedor.telefone = item.get('telefone', fornecedor.telefone)
                    atualizados += 1
                else:
                    # Criar
                    fornecedor = Fornecedor(
                        estabelecimento_id=estabelecimento_id,
                        nome_fantasia=nome,
                        razao_social=item.get('razao_social', nome),
                        cnpj=formatar_cnpj(cnpj_limpo) if cnpj_limpo else '00.000.000/0000-00', # Default se não tiver
                        email=item.get('email', 'sem@email.com'),
                        telefone=item.get('telefone', '00000000'),
                        cep=item.get('cep', '00000-000'),
                        logradouro=item.get('logradouro', 'Rua Desconhecida'),
                        numero=item.get('numero', 'S/N'),
                        bairro=item.get('bairro', 'Centro'),
                        cidade=item.get('cidade', 'Cidade'),
                        estado=item.get('estado', 'SP'),
                        ativo=True
                    )
                    db.session.add(fornecedor)
                    criados += 1
                    
            except Exception as e:
                erros.append(f"Linha {index+1}: {str(e)}")
                
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Importação concluída",
            "detalhes": {
                "criados": criados,
                "atualizados": atualizados,
                "erros": erros[:20]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na importação de fornecedores: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno na importação"}), 500
