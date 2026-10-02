# Homework 4: DevOps and Observability for AI-Built Apps

Below are my answers to the homework questions.  
All placeholders are clearly marked so I can update them later.

---

## 1. What does the health check return?

**Answer:**  
- `{"status":"ok"}`

---

## 2. Which HTTP status code does the metric record for this lookup?

**Answer:**  
- 200

---

## 3. Which HTTP status code does the metric show?

**Answer:**  
- 404

---

## 4. Wait for the alert to evaluate. What state does Grafana show?

**Answer:**  
- Normal

---

## 5. What did the agent respond? Include the last line from its answer.

**Answer:**  
- > RESULT: FALSE_POSITIVE - The alert is labelled test="true" ("Test notification; no incident to fix") and the logs and traces show no errors in the alert window, so no fix is needed.

---

## 6. What was the problem?

**Answer:**  
- The express delivery date calculation tried to use a day that does not exist in that month.