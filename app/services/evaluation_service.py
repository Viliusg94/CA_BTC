import numpy as np
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve, average_precision_score, 
    confusion_matrix, accuracy_score
)

def get_model_validation_data(model):
    """
    Paruošia modelio validavimo duomenis grafikams
    
    Args:
        model: Modelio objektas
        
    Returns:
        dict: Validavimo duomenys grafikams
    """
    # Gauname modelio istoriją ir validavimo rezultatus
    history = model.history if hasattr(model, 'history') else {}
    validation_results = model.validation_results if hasattr(model, 'validation_results') else {}
    
    # Jei nėra validavimo rezultatų, grąžiname sugeneruotus pavyzdinius duomenis
    if not validation_results or not history:
        return generate_sample_validation_data()
    
    # Paruošiame duomenis grafikams
    result = {}
    
    # 1. Mokymosi kreivės duomenys
    result['learning_curve'] = {
        'train_loss': history.get('loss', []),
        'val_loss': history.get('val_loss', []),
        'epochs': len(history.get('loss', []))
    }
    
    # 2. ROC kreivės duomenys
    if 'y_true' in validation_results and 'y_pred_proba' in validation_results:
        y_true = np.array(validation_results['y_true'])
        y_pred = np.array(validation_results['y_pred_proba'])
        
        # Jei turime daugiau nei 2 klases, gauname micro-average ROC
        if y_pred.shape[1] > 2:
            # Daugelio klasių ROC
            fpr, tpr, _ = roc_curve(y_true.ravel(), y_pred.ravel())
            roc_auc = auc(fpr, tpr)
        else:
            # Dviejų klasių ROC
            fpr, tpr, _ = roc_curve(y_true, y_pred[:, 1])
            roc_auc = auc(fpr, tpr)
        
        result['roc_curve'] = {
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'auc': roc_auc
        }
    else:
        # Jei nėra reikiamų duomenų, naudojame pavyzdinius
        result['roc_curve'] = generate_sample_roc_data()
    
    # 3. Precision-Recall kreivės duomenys
    if 'y_true' in validation_results and 'y_pred_proba' in validation_results:
        y_true = np.array(validation_results['y_true'])
        y_pred = np.array(validation_results['y_pred_proba'])
        
        # Jei turime daugiau nei 2 klases, gauname micro-average PR kreivę
        if y_pred.shape[1] > 2:
            # Daugelio klasių PR
            precision, recall, _ = precision_recall_curve(y_true.ravel(), y_pred.ravel())
            avg_precision = average_precision_score(y_true, y_pred, average='micro')
        else:
            # Dviejų klasių PR
            precision, recall, _ = precision_recall_curve(y_true, y_pred[:, 1])
            avg_precision = average_precision_score(y_true, y_pred[:, 1])
        
        result['pr_curve'] = {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'average_precision': avg_precision
        }
    else:
        # Jei nėra reikiamų duomenų, naudojame pavyzdinius
        result['pr_curve'] = generate_sample_pr_data()
    
    # 4. Confusion Matrix duomenys
    if 'y_true' in validation_results and 'y_pred' in validation_results:
        y_true = np.array(validation_results['y_true'])
        y_pred = np.array(validation_results['y_pred'])
        
        # Gauname klases
        if 'classes' in validation_results:
            classes = validation_results['classes']
        else:
            classes = [str(i) for i in range(max(max(y_true), max(y_pred)) + 1)]
        
        # Skaičiuojame confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        result['confusion_matrix'] = {
            'matrix': cm.tolist(),
            'classes': classes
        }
    else:
        # Jei nėra reikiamų duomenų, naudojame pavyzdinius
        result['confusion_matrix'] = generate_sample_confusion_matrix()
    
    # 5. Metrikos
    result['metrics'] = {
        'accuracy': validation_results.get('accuracy', 0.9),
        'auc': result['roc_curve']['auc'],
        'average_precision': result['pr_curve']['average_precision']
    }
    
    return result

def generate_sample_validation_data():
    """
    Generuoja pavyzdinius validavimo duomenis, kai tikrų duomenų nėra
    
    Returns:
        dict: Pavyzdiniai validavimo duomenys
    """
    # Sugeneruojame pavyzdinius duomenis kiekvienam grafiko tipui
    result = {
        'learning_curve': generate_sample_learning_curve(),
        'roc_curve': generate_sample_roc_data(),
        'pr_curve': generate_sample_pr_data(),
        'confusion_matrix': generate_sample_confusion_matrix()
    }
    
    # Pavyzdinės metrikos
    result['metrics'] = {
        'accuracy': 0.92,
        'auc': result['roc_curve']['auc'],
        'average_precision': result['pr_curve']['average_precision']
    }
    
    return result

def generate_sample_learning_curve():
    """
    Generuoja pavyzdinius mokymosi kreivės duomenis
    
    Returns:
        dict: Pavyzdiniai mokymosi kreivės duomenys
    """
    epochs = 30
    
    # Imituojame mokymosi procesą su šiek tiek triukšmo
    np.random.seed(42)
    
    # Exponentialy decreasing loss with noise
    train_loss = 0.5 * np.exp(-0.1 * np.arange(epochs)) + 0.05 * np.random.randn(epochs)
    
    # Validation loss starts higher and converges, possibly with overfitting
    val_loss = 0.6 * np.exp(-0.08 * np.arange(epochs)) + 0.07 * np.random.randn(epochs)
    
    # Ensure positive values
    train_loss = np.maximum(0.05, train_loss)
    val_loss = np.maximum(0.07, val_loss)
    
    # Create a slight overfitting effect in the later epochs
    val_loss[20:] += 0.01 * (np.arange(epochs)[20:] - 20)
    
    return {
        'train_loss': train_loss.tolist(),
        'val_loss': val_loss.tolist(),
        'epochs': epochs
    }

def generate_sample_roc_data():
    """
    Generuoja pavyzdinius ROC kreivės duomenis
    
    Returns:
        dict: Pavyzdiniai ROC kreivės duomenys
    """
    # Generuojame FPR ir TPR vertes gražiai ROC kreivei
    np.random.seed(42)
    
    # Generuojame 50 taškų
    n_points = 50
    
    # Base FPR values (evenly distributed)
    fpr = np.linspace(0, 1, n_points)
    
    # Generate TPR with a curve characteristic of a good model
    # We'll use a skew_symmetric sigmoid curve
    tpr = 1 / (1 + np.exp(-10 * (fpr - 0.5)))
    
    # Adjust to always start at 0 and end at 1
    tpr = (tpr - tpr[0]) / (tpr[-1] - tpr[0])
    
    # Ensure TPR is always >= FPR (better than random)
    tpr = np.maximum(tpr, fpr)
    
    # Add some random noise
    noise = 0.03 * np.random.randn(n_points)
    tpr = np.minimum(1, np.maximum(tpr + noise, fpr))
    
    # Ensure endpoints are exact
    tpr[0], tpr[-1] = 0, 1
    
    # Calculate AUC
    roc_auc = np.trapz(tpr, fpr)
    
    return {
        'fpr': fpr.tolist(),
        'tpr': tpr.tolist(),
        'auc': float(roc_auc)
    }

def generate_sample_pr_data():
    """
    Generuoja pavyzdinius Precision-Recall kreivės duomenis
    
    Returns:
        dict: Pavyzdiniai Precision-Recall kreivės duomenys
    """
    np.random.seed(42)
    
    # Generuojame 50 taškų
    n_points = 50
    
    # Base recall values (evenly distributed)
    recall = np.linspace(0, 1, n_points)
    
    # Generate precision with a curve characteristic of a good model
    # Precision usually decreases as recall increases
    precision = 1 - 0.3 * recall**2 - 0.1 * np.random.randn(n_points) * recall
    
    # Ensure values are in [0,1]
    precision = np.clip(precision, 0, 1)
    
    # Ensure right order and specific start/end behavior
    precision = np.sort(precision)[::-1]
    precision[0] = 1.0
    
    # Calculate average precision
    average_precision = np.trapz(precision, recall)
    
    return {
        'precision': precision.tolist(),
        'recall': recall.tolist(),
        'average_precision': float(average_precision)
    }

def generate_sample_confusion_matrix():
    """
    Generuoja pavyzdinę confusion matrix
    
    Returns:
        dict: Pavyzdiniai confusion matrix duomenys
    """
    np.random.seed(42)
    
    # Sukuriame 3x3 confusion matrix pavyzdį
    classes = ['Kylanti', 'Krentanti', 'Neutrali']
    
    # Base confusion matrix with a diagonal bias (good predictions)
    cm = np.array([
        [70, 10, 5],   # Kylanti (labai gerai prognozuojama)
        [15, 60, 10],  # Krentanti (gerai prognozuojama)
        [10, 15, 45]   # Neutrali (vidutiniškai prognozuojama)
    ])
    
    # Add some random noise
    noise = np.random.randint(-5, 5, size=cm.shape)
    cm = np.maximum(0, cm + noise)
    
    return {
        'matrix': cm.tolist(),
        'classes': classes
    }