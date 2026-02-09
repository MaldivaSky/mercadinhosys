import React from 'react';
import { X, Package, AlertTriangle } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';

interface ProductDetailsModalProps {
  productData: any;
  isOpen: boolean;
  onClose: () => void;
}

export const ProductDetailsModal: React.FC<ProductDetailsModalProps> = ({
  productData,
  isOpen,
  onClose
}) => {
  if (!isOpen || !productData) return null;

  const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', { 
    style: 'currency', currency: 'BRL' 
  }).format(val);

  const formatNumber = (val: number) => new Intl.NumberFormat('pt-BR').format(val);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6 text-indigo-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {productData.type === 'low_stock' ? 'Produtos com Estoque Crítico' : 'Detalhes do Produto'}
            </h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6">
          {productData.type === 'low_stock' ? (
            <div className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <h3 className="font-semibold text-amber-900 dark:text-amber-100">Alerta de Estoque</h3>
                </div>
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  {productData.products.length} produtos atingiram o nível crítico de estoque
                </p>
              </div>

              <div className="grid gap-3">
                {productData.products.map((product: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 border border-gray-200 dark:border-slate-700 rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">{product.nome}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Código: {product.codigo}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-4">
                        <div>
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {formatNumber(product.estoque_atual)}/{formatNumber(product.estoque_minimo)}
                          </span>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Atual/Mínimo</p>
                        </div>
                        <Badge 
                          variant={product.estoque_atual <= product.estoque_minimo ? 'destructive' : 'secondary'}
                          className="ml-2"
                        >
                          {product.estoque_atual <= product.estoque_minimo ? 'Crítico' : 'Atenção'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Informações do Produto</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Nome:</span> {productData.nome}</p>
                    <p><span className="font-medium">Código:</span> {productData.codigo}</p>
                    <p><span className="font-medium">Categoria:</span> {productData.categoria}</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Estoque</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Atual:</span> {formatNumber(productData.estoque_atual)}</p>
                    <p><span className="font-medium">Mínimo:</span> {formatNumber(productData.estoque_minimo)}</p>
                    <p><span className="font-medium">Status:</span> 
                      <Badge variant={productData.estoque_atual <= productData.estoque_minimo ? 'destructive' : 'default'} className="ml-2">
                        {productData.estoque_atual <= productData.estoque_minimo ? 'Crítico' : 'Normal'}
                      </Badge>
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Vendas</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Preço:</span> {formatCurrency(productData.preco)}</p>
                    <p><span className="font-medium">Custo:</span> {formatCurrency(productData.custo)}</p>
                    <p><span className="font-medium">Margem:</span> 
                      <Badge variant={((productData.preco - productData.custo) / productData.preco) > 0.3 ? 'default' : 'secondary'} className="ml-2">
                        {(((productData.preco - productData.custo) / productData.preco) * 100).toFixed(1)}%
                      </Badge>
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Desempenho</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Vendas (30d):</span> {formatNumber(productData.vendas_30d)}</p>
                    <p><span className="font-medium">Rotatividade:</span> 
                      <Badge variant={productData.rotatividade === 'alta' ? 'default' : 'secondary'} className="ml-2">
                        {productData.rotatividade}
                      </Badge>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-slate-700">
          <Button onClick={onClose} className="w-full">
            Fechar
          </Button>
        </div>
      </div>
    </div>
  );
};