with open('hmi/main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_ai_block = '''            # Check Fail-Safe before running AI
            if self._fail_safe.is_ai_allowed():
                # Strip Data Quality Score from AI features as the model was not trained on it
                ai_input = engineered_data.copy()
                ai_input.pop("Data Quality Score", None)
            
                # AI Optimization: Cache prediction to reduce CPU load
                if not hasattr(self, "_cached_ai_result") or self._cycle % 10 == 0:
                    ai_result = predict_plant_state(ai_input, self._lifecycle_engine)
                    self._cached_ai_result = ai_result
                else:
                    ai_result = self._cached_ai_result
            else:'''

new_ai_block = '''            # Check Fail-Safe before running AI
            if self._fail_safe.is_ai_allowed():
                ai_input = engineered_data.copy()
                ai_input.pop("Data Quality Score", None)
            
                # Async AI Worker
                if not hasattr(self, "_cached_ai_result"):
                    self._cached_ai_result = {
                        "Plant Status": "NORMAL", "Pump Failure Probability (%)": 0.0,
                        "Equipment Health (%)": 100.0, "Prediction Confidence (%)": 100.0
                    }
                if not hasattr(self, "_cached_shap_res"):
                    self._cached_shap_res = {"positive_factors": [], "negative_factors": [], "explanation_text": ""}

                if self._cycle % 10 == 0:
                    import threading
                    def _run_ai_async():
                        res = predict_plant_state(ai_input, self._lifecycle_engine)
                        shap = self._explainer.explain_prediction("GLOBAL", engineered_data, res["Pump Failure Probability (%)"])
                        self._cached_ai_result = res
                        self._cached_shap_res = shap
                    threading.Thread(target=_run_ai_async, daemon=True).start()
                
                ai_result = self._cached_ai_result
            else:'''
            
old_shap_block = '''            # 6. SHAP Explanation & Advanced Analytics
            if not hasattr(self, "_cached_shap_res") or self._cycle % 10 == 0:
                shap_res = self._explainer.explain_prediction("GLOBAL", engineered_data, ai_result["Pump Failure Probability (%)"])
                self._cached_shap_res = shap_res
            else:
                shap_res = self._cached_shap_res'''

new_shap_block = '''            # 6. SHAP Explanation & Advanced Analytics
            shap_res = getattr(self, "_cached_shap_res", {"positive_factors": [], "negative_factors": [], "explanation_text": ""})'''

if old_ai_block in content and old_shap_block in content:
    content = content.replace(old_ai_block, new_ai_block)
    content = content.replace(old_shap_block, new_shap_block)
    with open('hmi/main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Async AI patch applied.')
else:
    print('Blocks not found!')
