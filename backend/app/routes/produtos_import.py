

@produtos_bp.route("/import", methods=["POST"])
@funcionario_required
def importar_produtos():
    """Importa produtos via arquivo CSV ou Excel"""
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
                if not item.get('nome'):
                    erros.append(f"Linha {index+1}: Nome é obrigatório")
                    continue
                    
                # Normalização de dados
                codigo_barras = str(item.get('codigo_barras', '')).strip()
                codigo_interno = str(item.get('codigo_interno', '')).strip()
                
                # Procura produto existente
                produto = None
                if codigo_barras:
                    produto = Produto.query.filter_by(
                        estabelecimento_id=estabelecimento_id,
                        codigo_barras=codigo_barras
                    ).first()
                
                if not produto and codigo_interno:
                    produto = Produto.query.filter_by(
                        estabelecimento_id=estabelecimento_id,
                        codigo_interno=codigo_interno
                    ).first()
                    
                # Categoria
                categoria_id = None
                cat_nome = item.get('categoria', 'Geral')
                if cat_nome:
                    cat_nome_norm = CategoriaProduto.normalizar_nome_categoria(cat_nome)
                    categoria = CategoriaProduto.query.filter_by(
                        estabelecimento_id=estabelecimento_id,
                        nome=cat_nome_norm
                    ).first()
                    
                    if not categoria:
                        categoria = CategoriaProduto(
                            estabelecimento_id=estabelecimento_id,
                            nome=cat_nome_norm
                        )
                        db.session.add(categoria)
                        db.session.flush()
                        
                    categoria_id = categoria.id
                
                # Fornecedor (opcional, busca por nome)
                fornecedor_id = None
                forn_nome = item.get('fornecedor')
                if forn_nome:
                    fornecedor = Fornecedor.query.filter(
                        Fornecedor.estabelecimento_id == estabelecimento_id,
                        Fornecedor.nome_fantasia.ilike(f"%{forn_nome}%")
                    ).first()
                    if fornecedor:
                        fornecedor_id = fornecedor.id

                # Preços
                try:
                    preco_custo = Decimal(str(item.get('preco_custo', 0)).replace(',', '.'))
                    preco_venda = Decimal(str(item.get('preco_venda', 0)).replace(',', '.'))
                except:
                    preco_custo = Decimal(0)
                    preco_venda = Decimal(0)
                    
                # Margem
                if preco_custo > 0 and preco_venda > 0:
                    margem_lucro = ((preco_venda - preco_custo) / preco_custo) * 100
                else:
                    margem_lucro = Decimal(0)

                if produto:
                    # Atualizar
                    produto.nome = item.get('nome')
                    produto.descricao = item.get('descricao')
                    produto.preco_custo = preco_custo
                    produto.preco_venda = preco_venda
                    produto.margem_lucro = margem_lucro
                    if categoria_id: produto.categoria_id = categoria_id
                    if fornecedor_id: produto.fornecedor_id = fornecedor_id
                    
                    atualizados += 1
                else:
                    # Criar
                    produto = Produto(
                        estabelecimento_id=estabelecimento_id,
                        nome=item.get('nome'),
                        codigo_barras=codigo_barras,
                        codigo_interno=codigo_interno,
                        descricao=item.get('descricao'),
                        categoria_id=categoria_id,
                        fornecedor_id=fornecedor_id,
                        preco_custo=preco_custo,
                        preco_venda=preco_venda,
                        margem_lucro=margem_lucro,
                        quantidade=int(item.get('quantidade', 0)),
                        unidade_medida=item.get('unidade_medida', 'UN'),
                        marca=item.get('marca'),
                        ativo=True
                    )
                    db.session.add(produto)
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
                "erros": erros[:20]  # Limita retorno de erros
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na importação de produtos: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno na importação"}), 500
