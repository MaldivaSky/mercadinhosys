import re

file_path = "c:\\Users\\rafae\\OneDrive\\Desktop\\mercadinhosys\\frontend\\mercadinhosys-frontend\\src\\features\\dashboard\\DashboardPage.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Protect the already updated parts
parts = content.split("<!-- HEADER CIENTÍFICO -->", 1)
if len(parts) == 1:
    idx_visao_geral = content.find("VISÃO GERAL")
    header_content = content[:idx_visao_geral]
    rest_content = content[idx_visao_geral:]
else:
    header_content = "<!-- HEADER CIENTÍFICO -->\n" + parts[0]
    rest_content = parts[1]

# Apply substitutions on the rest
def replace(old, new, text):
    return text.replace(old, new)

text = rest_content

# Typography
text = re.sub(r'text-gray-900(?! dark:)', 'text-slate-900 dark:text-white', text)
text = re.sub(r'text-gray-800(?! dark:)', 'text-slate-800 dark:text-slate-200', text)
text = re.sub(r'text-gray-700(?! dark:)', 'text-slate-700 dark:text-slate-300', text)
text = re.sub(r'text-gray-600(?! dark:)', 'text-slate-600 dark:text-slate-400', text)
text = re.sub(r'text-gray-500(?! dark:)', 'text-slate-500 dark:text-slate-400', text)
text = re.sub(r'text-gray-400(?! dark:)', 'text-slate-400 dark:text-slate-500', text)
text = re.sub(r'text-gray-300(?! dark:)', 'text-slate-300 dark:text-slate-600', text)

# Backgrounds
text = re.sub(r'bg-white(?! dark:|/| border| rounded)', 'bg-white dark:bg-slate-900/50 backdrop-blur-xl', text)
text = re.sub(r'bg-white/70(?! dark:)', 'bg-white/70 dark:bg-slate-800/50 backdrop-blur-md', text)
text = re.sub(r'bg-white/80(?! dark:)', 'bg-white/80 dark:bg-slate-800/80 backdrop-blur-md', text)
text = re.sub(r'bg-gray-50(?! dark:)', 'bg-slate-50 dark:bg-slate-800/30', text)
text = re.sub(r'bg-gray-100(?! dark:)', 'bg-slate-100 dark:bg-slate-800', text)
text = re.sub(r'bg-gray-900/50(?! dark:)', 'bg-slate-900/50 dark:bg-slate-800/50', text)

# Borders
text = re.sub(r'border-gray-200(?! dark:)', 'border-slate-200 dark:border-slate-700/60', text)
text = re.sub(r'border-gray-300(?! dark:)', 'border-slate-300 dark:border-slate-600', text)
text = re.sub(r'border-gray-700(?! dark:)', 'border-slate-700 dark:border-slate-600', text)

# Cards & Effects
text = re.sub(r'rounded-xl shadow-lg(?! shadow-)', 'rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300', text)
text = re.sub(r'rounded-xl shadow-xl(?! hover:)', 'rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300', text)
text = re.sub(r'rounded-2xl shadow-xl(?! hover:)', 'rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300', text)

# Gradient containers (specific)
text = re.sub(r'from-green-50 to-emerald-50(?! dark:)', 'from-green-50 to-emerald-50 dark:from-green-900/10 dark:to-emerald-900/10', text)
text = re.sub(r'from-blue-50 to-cyan-50(?! dark:)', 'from-blue-50 to-cyan-50 dark:from-blue-900/10 dark:to-cyan-900/10', text)
text = re.sub(r'from-purple-50 to-pink-50(?! dark:)', 'from-purple-50 to-pink-50 dark:from-purple-900/10 dark:to-pink-900/10', text)
text = re.sub(r'from-indigo-50 to-purple-50(?! dark:)', 'from-indigo-50 to-purple-50 dark:from-indigo-900/10 dark:to-purple-900/10', text)
text = re.sub(r'from-orange-50 to-red-50(?! dark:)', 'from-orange-50 to-red-50 dark:from-orange-900/10 dark:to-red-900/10', text)
text = re.sub(r'from-cyan-50 to-blue-50(?! dark:)', 'from-cyan-50 to-blue-50 dark:from-cyan-900/10 dark:to-blue-900/10', text)

# Hover interactions
text = re.sub(r'cursor-pointer hover:bg-gray-50(?! dark:)', 'cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors', text)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(header_content + text)

print("Replacement complete.")
