import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import json

'''
FUNCIONES DE INICIALIZACIÓN Y ENTRENAMIENTO:
Las siguientes funciones están creadsas y se mantienen en el código para ser llamadas si se cambia el data_classified.json, pero si se mantiene igual, llamar a 
estas funciones no cambiará nada y solo consumirá recursos innecesarios. 
(Initilize models, prepare_data, train_models, train_logistic_regression, train_decision_tree, train_random_forest) 
'''

def initialize_models(get_absolute_path):
    models_dir = get_absolute_path('models')
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(get_absolute_path('static'), exist_ok=True)
    
    data_path = get_absolute_path('data_clasified.json')
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}")
        return False
    
    model_files = [
        os.path.join(models_dir, 'logistic_regression.pkl'),
        os.path.join(models_dir, 'decision_tree.pkl'),
        os.path.join(models_dir, 'random_forest.pkl')
    ]
    
    if all(os.path.exists(f) for f in model_files):
        return True
    
    try:
        success = train_models(get_absolute_path)
        return success
    except Exception as e:
        print(f"Error initializing models: {e}")
        return False


def prepare_data(get_absolute_path):
    try:
        data_path = get_absolute_path('data_clasified.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tickets = data.get('tickets_emitidos', [])
        if not tickets:
            print("No tickets found in JSON data")
            return None, None
            
        df = pd.DataFrame(tickets)
        
        df['cliente'] = df['cliente'].astype(int)
        df['es_mantenimiento'] = df['es_mantenimiento'].astype(int)
        df['tipo_incidencia'] = df['tipo_incidencia'].astype(int)
        
        df['tiempo_resolucion'] = np.nan
        for idx, row in df.iterrows():
            if row['fecha_apertura'] and row['fecha_cierre']:
                apertura = pd.to_datetime(row['fecha_apertura'])
                cierre = pd.to_datetime(row['fecha_cierre'])
                df.at[idx, 'tiempo_resolucion'] = (cierre - apertura).total_seconds() / 3600
        
        client_ticket_counts = df.groupby('cliente').size().reset_index(name='tickets_por_cliente')
        df = df.merge(client_ticket_counts, on='cliente', how='left')
        
        df['dia_semana'] = pd.to_datetime(df['fecha_apertura']).dt.dayofweek
        
        features = df[[
            'cliente', 'es_mantenimiento', 'tipo_incidencia', 
            'tiempo_resolucion', 'tickets_por_cliente', 'dia_semana'
        ]]
        
        features = features.fillna(features.mean())
        
        target = df['es_critico'].astype(int)
        
        return features, target
    except Exception as e:
        print(f"Error preparing data: {e}")
        return None, None


def train_models(get_absolute_path):
    features, target = prepare_data(get_absolute_path)
    if features is None:
        return False
    
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.3, random_state=42
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    joblib.dump(scaler, get_absolute_path('models/scaler.pkl'))
    
    train_logistic_regression(X_train_scaled, X_test_scaled, y_train, y_test, features, get_absolute_path)
    train_decision_tree(X_train, X_test, y_train, y_test, features, get_absolute_path)
    train_random_forest(X_train, X_test, y_train, y_test, features, get_absolute_path)
   
    return True


def train_logistic_regression(X_train_scaled, X_test_scaled, y_train, y_test, features, get_absolute_path):
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)
    lr_accuracy = accuracy_score(y_test, lr_preds)
    
    joblib.dump(lr_model, get_absolute_path('models/logistic_regression.pkl'))
    
    lr_importance = pd.DataFrame({
        'feature': features.columns,
        'importance': np.abs(lr_model.coef_[0])
    }).sort_values('importance', ascending=False)
    lr_importance.to_csv(get_absolute_path('models/lr_importance.csv'), index=False)
    
    plt.figure(figsize=(10, 6))
    plt.bar(lr_importance['feature'], lr_importance['importance'])
    plt.title(f'Logistic Regression Feature Importance (Accuracy: {lr_accuracy:.2f})')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(get_absolute_path('static/lr_importance.png'))
    plt.close()
    
    return lr_preds, lr_accuracy


def train_decision_tree(X_train, X_test, y_train, y_test, features, get_absolute_path):
    dt_model = DecisionTreeClassifier(random_state=42)
    dt_model.fit(X_train, y_train)
    dt_preds = dt_model.predict(X_test)
    dt_accuracy = accuracy_score(y_test, dt_preds)
    
    joblib.dump(dt_model, get_absolute_path('models/decision_tree.pkl'))
    
    dt_importance = pd.DataFrame({
        'feature': features.columns,
        'importance': dt_model.feature_importances_
    }).sort_values('importance', ascending=False)
    dt_importance.to_csv(get_absolute_path('models/dt_importance.csv'), index=False)
    
    plt.figure(figsize=(20, 12))
    plot_tree(dt_model, feature_names=features.columns, class_names=['No Crítico', 'Crítico'], 
              filled=True, rounded=True, max_depth=3)
    plt.title(f'Decision Tree Visualization (Accuracy: {dt_accuracy:.2f})')
    plt.tight_layout()
    plt.savefig(get_absolute_path('static/decision_tree.png'))
    plt.close()
    
    return dt_preds, dt_accuracy


def train_random_forest(X_train, X_test, y_train, y_test, features, get_absolute_path):
    rf_model = RandomForestClassifier(random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_accuracy = accuracy_score(y_test, rf_preds)
    
    joblib.dump(rf_model, get_absolute_path('models/random_forest.pkl'))
    
    rf_importance = pd.DataFrame({
        'feature': features.columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    rf_importance.to_csv(get_absolute_path('models/rf_importance.csv'), index=False)
    
    plt.figure(figsize=(10, 6))
    bars = plt.barh(rf_importance['feature'][::-1], rf_importance['importance'][::-1], 
             color='darkgreen', alpha=0.7)
    
    for i, bar in enumerate(bars):
        plt.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{rf_importance["importance"].iloc[::-1].iloc[i]:.3f}', 
                va='center', fontsize=9)
    
    plt.title(f'Random Forest Feature Importance (Accuracy: {rf_accuracy:.2f})')
    plt.xlabel('Relative Importance')
    plt.tight_layout()
    plt.savefig(get_absolute_path('static/rf_importance.png'))
    plt.close()
    
    plt.figure(figsize=(12, 8))
    plot_tree(rf_model.estimators_[0], max_depth=3, feature_names=features.columns,
              class_names=['No Crítico', 'Crítico'], filled=True, rounded=True)
    plt.title('Un árbol del bosque (Random Forest)')
    plt.tight_layout()
    plt.savefig(get_absolute_path('static/rf_sample_tree.png'))
    plt.close()
    
    return rf_preds, rf_accuracy


'''
FUNCIONES DE PREDICCIÓN:
Estas funciones si que son necesarias llamar para cada peticion POST:

1. prepare_features_for_prediction():
   - Procesa datos nuevos para cada predicción

2. predict_criticality():
   - Carga los modelos entrenados previamente para hacer predicciones
'''

def prepare_features_for_prediction(cliente_id, fecha_apertura, fecha_cierre, es_mantenimiento, tipo_incidencia, _, get_db_connection):
    con = get_db_connection()
    
    tiempo_resolucion = 0
    if fecha_apertura and fecha_cierre:
        apertura = pd.to_datetime(fecha_apertura)
        cierre = pd.to_datetime(fecha_cierre)
        tiempo_resolucion = (cierre - apertura).total_seconds() / 3600
    
    query = f"SELECT COUNT(*) as count FROM tickets_emitidos WHERE cliente = {cliente_id}"
    tickets_por_cliente = pd.read_sql(query, con).iloc[0]['count']
    
    dia_semana = pd.to_datetime(fecha_apertura).dayofweek
    
    con.close()
    
    features = pd.DataFrame({
        'cliente': [cliente_id],
        'es_mantenimiento': [es_mantenimiento],
        'tipo_incidencia': [tipo_incidencia],
        'tiempo_resolucion': [tiempo_resolucion],
        'tickets_por_cliente': [tickets_por_cliente],
        'dia_semana': [dia_semana]
    })
    
    return features


def predict_criticality(features, model_name, get_absolute_path):

    try:
        scaler = joblib.load(get_absolute_path('models/scaler.pkl'))
        
        if model_name == 'linear_regression' or model_name == 'logistic_regression':
            model_file = 'logistic_regression.pkl'
            importance_file = 'lr_importance.csv'
            features_scaled = scaler.transform(features)
            model = joblib.load(get_absolute_path(f'models/{model_file}'))
            prediction = model.predict(features_scaled)[0]
            confidence = model.predict_proba(features_scaled)[0][1] * 100
        elif model_name == 'decision_tree':
            model_file = 'decision_tree.pkl'
            importance_file = 'dt_importance.csv'
            model = joblib.load(get_absolute_path(f'models/{model_file}'))
            prediction = model.predict(features)[0]
            confidence = model.predict_proba(features)[0][1] * 100
        elif model_name == 'random_forest':
            model_file = 'random_forest.pkl'
            importance_file = 'rf_importance.csv'
            model = joblib.load(get_absolute_path(f'models/{model_file}'))
            prediction = model.predict(features)[0]
            confidence = model.predict_proba(features)[0][1] * 100
        else:
            return None, None, None
        
        try:
            importance_df = pd.read_csv(get_absolute_path(f'models/{importance_file}'))
            feature_importance = importance_df.to_dict('records')
        except:
            feature_importance = None
        
        return bool(prediction), confidence, feature_importance
    except Exception as e:
        import traceback
        print(f"Error en predict_criticality: {e}")
        print(f"Detalles: {traceback.format_exc()}")
        return None, None, None
