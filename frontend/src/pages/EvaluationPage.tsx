import Evaluation from '../components/Evaluation';

const EvaluationPage = () => {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-white mb-2">Evaluation Dashboard</h1>
        <p className="text-slate-400">Assess privacy protection and scene utility metrics for processed runs.</p>
      </div>
      
      <Evaluation />
      
      <div className="mt-8 p-6 rounded-2xl bg-indigo-900/10 border border-indigo-500/20">
        <h4 className="text-sm font-bold text-indigo-300 mb-2">Important Notice</h4>
        <p className="text-xs text-indigo-200/70 leading-relaxed">
          These evaluation metrics are experimental indicators designed to provide relative comparisons between different anonymization techniques. They do not constitute a mathematical guarantee of anonymity or perfect privacy. Real-world deployment requires comprehensive adversarial testing.
        </p>
      </div>
    </div>
  );
};

export default EvaluationPage;
