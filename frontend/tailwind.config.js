/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'azul-principal': '#1E40AF',
                'verde-positivo': '#059669',
                'laranja-alerta': '#EA580C',
            }
        },
    },
    plugins: [],
}

module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {},
    },
    plugins: [],
}