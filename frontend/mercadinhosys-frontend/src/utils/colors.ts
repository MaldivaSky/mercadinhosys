/**
 * MercadinhoSys - Utilitários de Cor Dinâmica
 * Gera paletas de cores HSL para gráficos e UI
 * Elimina cores fixas e garante consistência visual
 */

/**
 * Gera cor HSL baseada no índice
 * @param index - Índice do item (0, 1, 2, ...)
 * @param total - Total de itens
 * @param saturation - Saturação (default: 70%)
 * @param lightness - Luminosidade (default: 55%)
 * @returns string HSL
 */
export const generateHSLColor = (
  index: number,
  total: number,
  saturation: number = 70,
  lightness: number = 55
): string => {
  if (total <= 0) return `hsl(0, ${saturation}%, ${lightness}%)`;

  const hue = (index * 360) / total;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

/**
 * Gera paleta de cores completa para um dataset
 * @param data - Array de dados
 * @param saturation - Saturação opcional
 * @param lightness - Luminosidade opcional
 * @returns Array de cores HSL
 */
export const generateColorPalette = (
  data: any[],
  saturation: number = 70,
  lightness: number = 55
): string[] => {
  if (!data || data.length === 0) return [];

  return data.map((_, index) =>
    generateHSLColor(index, data.length, saturation, lightness)
  );
};

/**
 * Gera paleta para gráficos de categorias
 * Cores mais vibrantes para melhor distinção
 */
export const generateCategoryColors = (categories: string[]): Record<string, string> => {
  const colors: Record<string, string> = {};

  categories.forEach((category, index) => {
    colors[category] = generateHSLColor(index, categories.length, 75, 50);
  });

  return colors;
};

/**
 * Gera cores para gráficos financeiros
 * Tons de verde/azul para positivos, vermelho para negativos
 */
export const generateFinancialColors = (
  hasNegative: boolean = false
): { positive: string; negative?: string; neutral: string } => {
  return {
    positive: generateHSLColor(120, 360, 60, 50), // Verde
    neutral: generateHSLColor(200, 360, 65, 55),  // Azul
    negative: hasNegative ? generateHSLColor(0, 360, 70, 50) : undefined // Vermelho
  };
};

/**
 * Gera cores para status (ativos/inativos)
 */
export const generateStatusColors = (): {
  active: string;
  inactive: string;
  pending: string;
  warning: string;
  error: string;
} => {
  return {
    active: generateHSLColor(120, 360, 60, 45),    // Verde
    inactive: generateHSLColor(0, 360, 0, 75),      // Cinza
    pending: generateHSLColor(45, 360, 90, 55),     // Laranja
    warning: generateHSLColor(30, 360, 85, 50),     // Amarelo
    error: generateHSLColor(0, 360, 70, 45)         // Vermelho
  };
};

/**
 * Configurações padrão para Chart.js com cores dinâmicas
 */
export const getDynamicChartConfig = (
  data: any[],
  type: 'bar' | 'line' | 'doughnut' | 'pie' = 'bar'
) => {
  const colors = generateColorPalette(data);

  const baseConfig = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            family: "'Inter', sans-serif"
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: function (context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
              }).format(context.parsed.y);
            }
            return label;
          }
        }
      }
    }
  };

  // Configurações específicas por tipo
  switch (type) {
    case 'doughnut':
    case 'pie':
      return {
        ...baseConfig,
        plugins: {
          ...baseConfig.plugins,
          legend: {
            ...baseConfig.plugins.legend,
            position: 'right' as const
          }
        },
        cutout: '75%', // Donut style
        data: {
          datasets: [{
            data: data.map(item => item.value || item.y || 0),
            backgroundColor: colors,
            borderColor: '#fff',
            borderWidth: 2
          }]
        }
      };

    case 'line':
      return {
        ...baseConfig,
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 11
              }
            }
          },
          y: {
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              font: {
                size: 11
              },
              callback: function (value: any) {
                return new Intl.NumberFormat('pt-BR', {
                  style: 'currency',
                  currency: 'BRL'
                }).format(value);
              }
            }
          }
        },
        elements: {
          line: {
            tension: 0.4,
            borderWidth: 3
          },
          point: {
            radius: 5,
            hoverRadius: 7,
            backgroundColor: '#fff',
            borderWidth: 2
          }
        }
      };

    case 'bar':
    default:
      return {
        ...baseConfig,
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 11
              }
            }
          },
          y: {
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              font: {
                size: 11
              },
              callback: function (value: any) {
                return new Intl.NumberFormat('pt-BR', {
                  style: 'currency',
                  currency: 'BRL'
                }).format(value);
              }
            }
          }
        },
        elements: {
          bar: {
            borderRadius: 6,
            borderSkipped: false
          }
        }
      };
  }
};

/**
 * Utilitário para tratar dados ausentes em gráficos
 */
export const handleEmptyData = (
  data: any[],
  defaultMessage: string = 'Sem movimentação'
): any[] => {
  if (!data || data.length === 0) {
    return [{
      label: defaultMessage,
      value: 0,
      y: 0
    }];
  }

  return data.map(item => ({
    ...item,
    value: item.value || item.y || 0,
    label: item.label || item.name || 'Sem nome'
  }));
};

/**
 * Cores padrão do sistema (geradas dinamicamente)
 */
export const systemColors = {
  primary: generateHSLColor(220, 360, 70, 55),      // Azul principal
  secondary: generateHSLColor(200, 360, 65, 55),    // Azul secundário
  success: generateHSLColor(120, 360, 60, 45),      // Verde
  warning: generateHSLColor(30, 360, 85, 50),       // Amarelo
  danger: generateHSLColor(0, 360, 70, 45),         // Vermelho
  info: generateHSLColor(200, 360, 75, 55),         // Azul claro
  light: generateHSLColor(0, 360, 0, 95),           // Branco
  dark: generateHSLColor(0, 360, 0, 20)            // Preto
};

export default {
  generateHSLColor,
  generateColorPalette,
  generateCategoryColors,
  generateFinancialColors,
  generateStatusColors,
  getDynamicChartConfig,
  handleEmptyData,
  systemColors
};
