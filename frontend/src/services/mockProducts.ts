// Dados de exemplo para teste

export interface MockProduct {
    id: string;
    name: string;
    barcode?: string;
    price: number;
    stock: number;
    isBulk?: boolean;
    unit?: string;
}

// Dados de exemplo para teste
export const mockProducts: MockProduct[] = [
    {
        id: '1',
        name: 'Arroz Branco 5kg',
        barcode: '7891000315507',
        price: 24.90,
        stock: 50,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '2',
        name: 'Feijão Carioca 1kg',
        barcode: '7891000055502',
        price: 8.90,
        stock: 100,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '3',
        name: 'Açúcar Cristal 1kg',
        barcode: '7891000088807',
        price: 4.50,
        stock: 80,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '4',
        name: 'Café em Pó 500g',
        barcode: '7891000123456',
        price: 18.90,
        stock: 40,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '5',
        name: 'Óleo de Soja 900ml',
        barcode: '7891000156789',
        price: 7.90,
        stock: 60,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '6',
        name: 'Leite Integral 1L',
        barcode: '7891000189012',
        price: 5.90,
        stock: 120,
        isBulk: false,
        unit: 'un'
    },
    {
        id: '7',
        name: 'Pão Francês',
        price: 0.50,
        stock: 200,
        isBulk: true,
        unit: 'un'
    },
    {
        id: '8',
        name: 'Queijo Mussarela',
        barcode: '7891000255555',
        price: 42.90,
        stock: 25,
        isBulk: true,
        unit: 'kg'
    },
    {
        id: '9',
        name: 'Presunto',
        barcode: '7891000288888',
        price: 36.90,
        stock: 30,
        isBulk: true,
        unit: 'kg'
    },
    {
        id: '10',
        name: 'Banana',
        price: 3.90,
        stock: 150,
        isBulk: true,
        unit: 'kg'
    }
];

export default mockProducts;