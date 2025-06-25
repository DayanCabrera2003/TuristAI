import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Configuración de estilo
try:
    plt.style.use('seaborn-v0_8')  # Intenta con el nuevo nombre
except:
    plt.style.use('ggplot')  # Usa otro estilo si el anterior falla
sns.set_palette("husl")

# Datos
data = {
    'Itinerario': range(1, 11),
    'Formulario': [1350.0, 1350.0, 1351.0, 1320.0, 1290.0, 1320.0, 1321.0, 1290.0, 1260.0, 1290.0],
    'Lenguaje_natural': [1350.0, 1351.0, 1351.0, 1260.0, 0.0, 901.0, 1321.0, 1230.0, 1230.0, 0.0]
}

def normalize_scale(df, columns, scale_factor=100):
    """Divide los valores por un factor de escala"""
    df_normalized = df.copy()
    
    for col in columns:
        df_normalized[col] = df[col] / scale_factor
    
    return df_normalized

df = pd.DataFrame(data)
print("Datos originales:")
print(df)

# Ahora normalizar
columns_to_normalize = ['Formulario', 'Lenguaje_natural']
df = normalize_scale(df, columns_to_normalize)

print("\nDatos normalizados:")
print(df.round(2))

# Estadísticas descriptivas
stats_formulario = df['Formulario'].describe()
stats_lenguaje = df['Lenguaje_natural'].describe()

stats_comparativas = pd.DataFrame({
    'Formulario': stats_formulario,
    'Lenguaje Natural': stats_lenguaje
})

print("Estadísticas Comparativas:")
print(stats_comparativas.round(2))

plt.figure(figsize=(12, 6))
bar_width = 0.35
index = np.arange(len(df))

bars1 = plt.bar(index, df['Formulario'], bar_width, label='Formulario')
bars2 = plt.bar(index + bar_width, df['Lenguaje_natural'], bar_width, label='Lenguaje Natural')

plt.xlabel('Itinerario')
plt.ylabel('Puntuación de Calidad')
plt.title('Comparación de Calidad: Formulario vs. Lenguaje Natural')
plt.xticks(index + bar_width / 2, df['Itinerario'])
plt.legend()
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
df_melted = df.melt(id_vars=['Itinerario'], value_vars=['Formulario', 'Lenguaje_natural'], 
                    var_name='Método', value_name='Puntuación')

sns.boxplot(x='Método', y='Puntuación', data=df_melted)
plt.title('Distribución de Puntuaciones por Método')
plt.show()


df['Diferencia'] = df['Formulario'] - df['Lenguaje_natural']

plt.figure(figsize=(10, 5))
plt.bar(df['Itinerario'], df['Diferencia'], color=np.where(df['Diferencia']>0, 'blue', 'red'))
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Itinerario')
plt.ylabel('Diferencia (Formulario - Lenguaje Natural)')
plt.title('Diferencias en Puntuación entre Métodos')
plt.show()


# Crear tabla resumen
summary_table = df.copy()
summary_table['Diferencia'] = summary_table['Formulario'] - summary_table['Lenguaje_natural']
summary_table['Porcentaje_Diferencia'] = (summary_table['Diferencia'] / summary_table['Formulario']) * 100

print("\nTabla Comparativa Detallada:")
print(summary_table.round(2))