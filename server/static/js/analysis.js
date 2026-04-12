/**
 * SQLOps Oracle — ML Analysis Engine
 * Designed by K. Ajay John Paul | KL University Hyderabad
 */

class SQLOpsAnalysis {
  constructor(sampleData) { this.data = sampleData; }

  learningCurveSlope(rewards) {
    const n = rewards.length; if (n < 2) return 0;
    const xs = rewards.map((_, i) => i);
    const sx = xs.reduce((a, b) => a + b, 0);
    const sy = rewards.reduce((a, b) => a + b, 0);
    const sxy = xs.reduce((a, x, i) => a + x * rewards[i], 0);
    const sx2 = xs.reduce((a, x) => a + x * x, 0);
    return Math.round(((n * sxy - sx * sy) / (n * sx2 - sx * sx)) * 1000) / 1000;
  }

  efficiencyScore(bestScore, attemptsUsed, maxAttempts) {
    return Math.round((bestScore * (maxAttempts - attemptsUsed + 1) / maxAttempts) * 100) / 100;
  }

  rSquared(rewards) {
    const n = rewards.length;
    const mean = rewards.reduce((a, b) => a + b, 0) / n;
    const slope = this.learningCurveSlope(rewards);
    const intercept = mean - slope * (n - 1) / 2;
    const ssTot = rewards.reduce((a, v) => a + (v - mean) ** 2, 0);
    const ssRes = rewards.reduce((a, v, i) => a + (v - (slope * i + intercept)) ** 2, 0);
    return ssTot === 0 ? 1 : Math.max(0, Math.round((1 - ssRes / ssTot) * 100) / 100);
  }

  predictAttemptsToScore(rewards, targetScore) {
    const slope = this.learningCurveSlope(rewards);
    if (slope <= 0) return null;
    const last = rewards[rewards.length - 1];
    return Math.max(1, Math.ceil((targetScore - last) / slope));
  }

  generateInsights(taskResults) {
    const insights = [];
    const totalTasks = taskResults.length;
    const solved = taskResults.filter(t => t.finalScore >= 0.9).length;
    insights.push({
      type: 'performance', icon: '\u25C6',
      text: `Agent solved ${solved}/${totalTasks} tasks with perfect scores`,
      detail: `Overall accuracy: ${Math.round(solved / totalTasks * 100)}%`
    });

    const allRewards = taskResults.flatMap(t => t.rewards);
    const slope = this.learningCurveSlope(allRewards);
    insights.push({
      type: 'learning', icon: '\u25C7',
      text: `Learning velocity: ${slope > 0 ? '+' : ''}${slope} reward/attempt`,
      detail: slope > 0.15 ? 'Strong upward trajectory \u2014 model adapts quickly' :
              slope > 0.05 ? 'Moderate learning \u2014 consistent improvement' :
              'Slow learning \u2014 consider larger model or better prompting'
    });

    const hardTask = taskResults.reduce((a, b) => a.attempts > b.attempts ? a : b);
    const recRate = hardTask.errors > 0 ? Math.round(hardTask.recoveries / hardTask.errors * 100) : 100;
    insights.push({
      type: 'difficulty', icon: '\u25CB',
      text: `Most challenging: ${hardTask.taskId} (${hardTask.attempts} attempts)`,
      detail: `Error recovery rate: ${recRate}%`
    });

    const avgEff = taskResults.reduce((a, t) =>
      a + this.efficiencyScore(t.finalScore, t.attempts, t.maxAttempts), 0) / totalTasks;
    insights.push({
      type: 'efficiency', icon: '\u25A1',
      text: `Agent efficiency score: ${avgEff.toFixed(2)}/1.00`,
      detail: avgEff > 0.8 ? 'Excellent \u2014 solved with few attempts remaining' :
              avgEff > 0.6 ? 'Good \u2014 room for prompt optimization' :
              'Needs improvement \u2014 agent exhausted most attempts'
    });

    return insights;
  }
}

/* ── SAMPLE DATA (pre-loaded for demo) ── */
window.SAMPLE_DATA = {
  taskResults: [
    {
      taskId: 'sales_summary', difficulty: 'easy', maxAttempts: 5,
      attempts: 4, finalScore: 1.00,
      rewards: [0.15, 0.30, 0.75, 1.00],
      errors: 0, recoveries: 0,
      sqls: [
        "SELECT name, SUM(amount) FROM sales GROUP BY name",
        "SELECT d.name as department_name, SUM(s.amount) as total_amount FROM departments d JOIN employees e ON d.id=e.department_id JOIN sales s ON s.employee_id=e.id GROUP BY d.id",
        "SELECT d.name as department_name, ROUND(SUM(s.amount),2) as total_amount, COUNT(s.id) as transaction_count FROM departments d JOIN employees e ON d.id=e.department_id JOIN sales s ON s.employee_id=e.id GROUP BY d.id,d.name ORDER BY total_amount DESC",
        "SELECT region, ROUND(SUM(amount),2) AS total_revenue, SUM(quantity) AS total_quantity FROM sales GROUP BY region ORDER BY total_revenue DESC"
      ],
      departmentData: [
        { label: 'Engineering',      value: 2847320 },
        { label: 'Sales',            value: 2654180 },
        { label: 'Product',          value: 1923450 },
        { label: 'Marketing',        value: 1654230 },
        { label: 'Operations',       value: 1432100 },
        { label: 'Finance',          value: 1287640 },
        { label: 'Customer Success', value: 1198750 },
        { label: 'HR',               value: 876540  },
        { label: 'Design',           value: 754320  },
        { label: 'Legal',            value: 432180  },
      ]
    },
    {
      taskId: 'debug_query', difficulty: 'medium', maxAttempts: 7,
      attempts: 6, finalScore: 1.00,
      rewards: [0.00, 0.20, 0.40, 0.60, 0.80, 1.00],
      errors: 1, recoveries: 1,
      sqls: [
        "SELECT d.name, COUNT(pa.status) FROM departments d JOIN projects p ON d.id=p.department_id JOIN project_assignments pa ON p.id=pa.project_id GROUP BY d.name",
        "SELECT d.name AS department, COUNT(p.id) AS active_projects FROM departments d JOIN projects p ON d.id = p.department_id WHERE p.status = 'active' GROUP BY d.name",
        "SELECT d.name AS department, COUNT(p.id) AS active_projects FROM departments d LEFT JOIN projects p ON d.id = p.department_id WHERE p.status = 'active' GROUP BY d.name",
        "SELECT d.name AS department, COUNT(p.id) AS active_projects FROM departments d LEFT JOIN projects p ON d.id = p.department_id AND p.status = 'active' GROUP BY d.name",
        "SELECT d.name AS department, COUNT(p.id) AS active_projects FROM departments d LEFT JOIN projects p ON d.id = p.department_id AND p.status = 'active' GROUP BY d.name ORDER BY active_projects",
        "SELECT d.name AS department, COUNT(p.id) AS active_projects FROM departments d LEFT JOIN projects p ON d.id = p.department_id AND p.status = 'active' GROUP BY d.name ORDER BY active_projects DESC, d.name ASC"
      ],
      debugBugs: [
        { bug: 'pa.status column does not exist', fixed: true, attempt: 2 },
        { bug: 'WHERE clause breaks LEFT JOIN', fixed: true, attempt: 4 },
        { bug: 'Missing ORDER BY direction', fixed: true, attempt: 6 },
      ]
    },
    {
      taskId: 'performance_analytics', difficulty: 'hard', maxAttempts: 10,
      attempts: 9, finalScore: 1.00,
      rewards: [0.00, 0.00, 0.25, 0.40, 0.55, 0.70, 0.85, 0.85, 1.00],
      errors: 2, recoveries: 2,
      sqls: [
        "WITH dept AS SELECT * FROM departments",
        "SELECT employee_id, ROW_NUMBER() OVER (ORDER BY rating) FROM performance_reviews",
        "SELECT d.name, AVG(pr.rating) AS avg_rating FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name",
        "SELECT d.name AS department, AVG(pr.rating) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name",
        "WITH dept_ratings AS (SELECT d.name AS department, AVG(pr.rating) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name) SELECT * FROM dept_ratings ORDER BY avg_rating DESC",
        "WITH dept_ratings AS (SELECT d.name AS department, ROUND(AVG(pr.rating),2) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name HAVING COUNT(pr.id) >= 2) SELECT department, avg_rating, review_count FROM dept_ratings ORDER BY avg_rating DESC",
        "WITH dept_ratings AS (SELECT d.name AS department, ROUND(AVG(pr.rating),2) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name HAVING COUNT(pr.id) >= 2) SELECT department, avg_rating, review_count, RANK() OVER (ORDER BY avg_rating DESC) AS dept_rank FROM dept_ratings",
        "WITH dept_ratings AS (SELECT d.name AS department, ROUND(AVG(pr.rating),2) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name HAVING COUNT(pr.id) >= 2) SELECT department, avg_rating, review_count, RANK() OVER (ORDER BY avg_rating DESC) AS dept_rank FROM dept_ratings",
        "WITH dept_ratings AS (SELECT d.name AS department, ROUND(AVG(pr.rating),2) AS avg_rating, COUNT(pr.id) AS review_count FROM performance_reviews pr JOIN employees e ON pr.employee_id = e.id JOIN departments d ON e.department_id = d.id GROUP BY d.name HAVING COUNT(pr.id) >= 2) SELECT department, avg_rating, review_count, RANK() OVER (ORDER BY avg_rating DESC) AS dept_rank FROM dept_ratings ORDER BY dept_rank ASC"
      ],
      topEmployees: [
        { dept: 'Engineering',      name: 'Ananya K.', rating: 4.92, rank: 1 },
        { dept: 'Engineering',      name: 'Vikram I.',  rating: 4.83, rank: 2 },
        { dept: 'Customer Success', name: 'Priya S.',   rating: 4.89, rank: 1 },
        { dept: 'Customer Success', name: 'Arjun R.',   rating: 4.75, rank: 2 },
      ]
    }
  ],
  overallMetrics: {
    totalSteps: 19, totalAttempts: 19, perfectScores: 3,
    avgAttemptsToSolve: 6.33, learningSlope: 0.18,
    errorRecoveryRate: 1.00, efficiencyScore: 0.89, finalScore: 1.00
  }
};

window.sqlAnalysis = new SQLOpsAnalysis(window.SAMPLE_DATA);
