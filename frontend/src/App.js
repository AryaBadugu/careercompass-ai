import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Loader2, Target, Search, BarChart3, Trophy, Calendar, CheckCircle2, User, Sparkles, Briefcase, Clock, TrendingUp, Heart, Code } from 'lucide-react';
import './App.css';

const STEP_NAMES = {
  1: "👤 Profile Analysis",
  2: "🗺️ Career Path Search",
  3: "📊 Skills Gap Analysis",
  4: "🏆 Opportunity Ranking",
  5: "📅 Roadmap Creation",
  6: "✅ Final Action Plan"
};

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ERROR_MESSAGES = {
  empty: '📝 Please describe your profile in more detail (at least 20 characters)',
  network: '🌐 Connection error. Check your internet and try again.',
  timeout: '⏱️ Request timed out. Agent is thinking too long. Try a shorter profile.',
  server: `⚙️ Server error. Make sure your FastAPI backend is running on ${API_BASE_URL}`,
  unknown: '❌ Something went wrong. Please try again.'
};

const LOADING_MESSAGES = {
  0: { text: "Initializing reasoning engine...", icon: Sparkles },
  1: { text: "Analyzing your profile and identifying core skills...", icon: User },
  2: { text: "Searching global career databases for top matches...", icon: Search },
  3: { text: "Computing skill gaps and transition readiness...", icon: BarChart3 },
  4: { text: "Ranking opportunities by demand and feasibility...", icon: Trophy },
  5: { text: "Structuring a personalized 90-day roadmap...", icon: Calendar },
  6: { text: "Finalizing your actionable career strategy...", icon: CheckCircle2 }
};

function App() {
  const [profile, setProfile] = useState('');
  const [steps, setSteps] = useState([]);
  const [fullResponse, setFullResponse] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [regenerating, setRegenerating] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [career1, setCareer1] = useState('');
  const [career2, setCareer2] = useState('');
  const [comparisonResult, setComparisonResult] = useState('');
  const [comparing, setComparing] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingChecklist, setExportingChecklist] = useState(false);
  const [marketDemand, setMarketDemand] = useState(null);
  const [analyzingDemand, setAnalyzingDemand] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState('');

  const analyzeProfile = async () => {
    if (!profile || profile.length < 20) {
      setError(ERROR_MESSAGES.empty);
      return;
    }

    setLoading(true);
    setSteps([]);
    setFullResponse('');
    setError('');
    setCurrentStep(0);

    const stepTimer = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= 5) {
          clearInterval(stepTimer);
          return prev;
        }
        return prev + 1;
      });
    }, 4000);

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, {
        profile: profile
      }, {
        timeout: 120000 // 2 minute timeout for agent reasoning
      });

      clearInterval(stepTimer);
      setCurrentStep(6);
      setSteps(response.data.steps);
      setFullResponse(response.data.full_response);
      setShowFeedback(false);
      setFeedback('');
      setComparisonMode(false);
      setCareer1('');
      setCareer2('');
      setComparisonResult('');
      setExportingPdf(false);
      setExportingChecklist(false);
      setMarketDemand(null);
      setAnalyzingDemand(false);
    } catch (err) {
      clearInterval(stepTimer);

      let errorMsg = ERROR_MESSAGES.unknown;
      if (err.code === 'ECONNABORTED') {
        errorMsg = ERROR_MESSAGES.timeout;
      } else if (err.message === 'Network Error') {
        errorMsg = ERROR_MESSAGES.network;
      } else if (err.response?.status === 500) {
        errorMsg = ERROR_MESSAGES.server;
      }

      setError(errorMsg);
      console.error('Full error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    setComparing(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/compare`, {
        career1,
        career2
      });
      setComparisonResult(response.data.comparison);
    } catch (err) {
      setError('Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const handleRegenerateWithFeedback = async () => {
    setRegenerating(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/regenerate`, {
        original_profile: profile,
        feedback: feedback
      });

      setFullResponse(response.data.regenerated_response);
      setFeedback('');
      setShowFeedback(false);
    } catch (err) {
      setError('Failed to regenerate. Try again.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey && !loading) {
      analyzeProfile();
    }
  };

  const handleExportPdf = async () => {
    if (!profile) return;
    setExportingPdf(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/export-pdf`,
        { profile },
        { responseType: 'blob' }
      );

      const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `CareerCompass_Analysis_${Date.now()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError('Could not export PDF report. Please try again.');
    } finally {
      setExportingPdf(false);
    }
  };

  const handleExportChecklist = async () => {
    if (!profile) return;
    setExportingChecklist(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/export-skills-checklist`,
        { profile },
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `CareerCompass_Skills_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError('Could not export checklist. Please try again.');
    } finally {
      setExportingChecklist(false);
    }
  };

  const getSkillCandidatesForDemand = () => {
    const baseSkills = parseProfileSummary(getStepOutput(1)).skills;
    const gapTitles = parseGapLines(getStepOutput(3)).map((gap) => gap.title);

    const combined = [...baseSkills, ...gapTitles]
      .map((item) => item.trim())
      .filter((item) => item && item.length >= 2);

    const unique = [];
    const seen = new Set();
    for (const skill of combined) {
      const key = skill.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(skill);
      }
    }

    return unique.slice(0, 8);
  };

  const handleAnalyzeMarketDemand = async () => {
    const skills = getSkillCandidatesForDemand();
    if (skills.length === 0) {
      setError('No skills found yet. Run analysis first.');
      return;
    }

    setAnalyzingDemand(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/market-demand`, { skills });
      setMarketDemand(response.data);
    } catch (err) {
      setError('Could not fetch live market demand. Please try again.');
    } finally {
      setAnalyzingDemand(false);
    }
  };

  const normalizeStepOutput = (output) => {
    if (!output) return '';
    return output.replace(/^STEP\s+\d+\s+COMPLETE:\s*/i, '').trim();
  };

  const parseBracketList = (value = '') => {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  };

  const parseProfileSummary = (text) => {
    const clean = normalizeStepOutput(text);
    const skillsMatch = clean.match(/Skills=\[(.*?)\]/i);
    const goalsMatch = clean.match(/Goals=\[(.*?)\]/i);
    const educationMatch = clean.match(/Education=(.*?)(?:,\s*Experience=|$)/i);
    const experienceMatch = clean.match(/Experience=(.*)$/i);

    return {
      skills: skillsMatch ? parseBracketList(skillsMatch[1]) : [],
      goals: goalsMatch ? parseBracketList(goalsMatch[1]) : [],
      education: educationMatch ? educationMatch[1].trim() : '',
      experience: experienceMatch ? experienceMatch[1].trim() : ''
    };
  };

  const parseCareerList = (text) => {
    const clean = normalizeStepOutput(text);
    const careersMatch = clean.match(/\[(.*?)\]/);
    return careersMatch ? parseBracketList(careersMatch[1]) : [];
  };

  const parseGapLines = (text) => {
    return normalizeStepOutput(text)
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.startsWith('-'))
      .map((line) => {
        const stripped = line.replace(/^-\s*/, '');
        const separatorIndex = stripped.indexOf(':');
        if (separatorIndex === -1) {
          return { title: 'Skill Gap', detail: stripped };
        }
        return {
          title: stripped.slice(0, separatorIndex).trim(),
          detail: stripped.slice(separatorIndex + 1).trim()
        };
      });
  };

  const parseRankings = (text) => {
    const clean = normalizeStepOutput(text);
    const rankingMatch = clean.match(/\[(.*?)\]/);
    if (!rankingMatch) return [];

    return rankingMatch[1]
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
      .map((entry) => {
        const parts = entry.split(':');
        if (parts.length < 2) return null;
        const title = parts[0].trim();
        const scoreText = parts[1].trim();
        const scoreMatch = scoreText.match(/(\d+)\s*\/\s*10/);
        const score = scoreMatch ? Number(scoreMatch[1]) : 0;
        return { title, score, scoreText };
      })
      .filter(Boolean);
  };

  const parseRoadmapPhases = (text) => {
    const cleanLines = normalizeStepOutput(text)
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

    const phases = [
      { key: '30', label: 'Phase 1', period: '0-30 Days', items: [] },
      { key: '60', label: 'Phase 2', period: '31-60 Days', items: [] },
      { key: '90', label: 'Phase 3', period: '61-90 Days', items: [] }
    ];

    let activePhase = null;

    const detectPhase = (line) => {
      const normalized = line.toLowerCase();
      if (/(30\s*[-/]?\s*day|first\s*30|phase\s*1|month\s*1|week\s*1)/i.test(normalized)) return phases[0];
      if (/(60\s*[-/]?\s*day|second\s*30|phase\s*2|month\s*2|week\s*2)/i.test(normalized)) return phases[1];
      if (/(90\s*[-/]?\s*day|third\s*30|phase\s*3|month\s*3|week\s*3)/i.test(normalized)) return phases[2];
      return null;
    };

    cleanLines.forEach((line) => {
      const phase = detectPhase(line);
      if (phase) {
        activePhase = phase;
        const afterColon = line.includes(':') ? line.split(':').slice(1).join(':').trim() : '';
        if (afterColon) {
          phase.items.push(afterColon.replace(/^[-*]\s*/, ''));
        }
        return;
      }

      const itemText = line.replace(/^[-*]\s*/, '').replace(/^\d+[.)]\s*/, '').trim();
      if (!itemText) return;

      if (!activePhase) {
        activePhase = phases[0];
      }

      activePhase.items.push(itemText);
    });

    if (phases.every((phase) => phase.items.length === 0)) {
      const fallbackItems = cleanLines
        .map((line) => line.replace(/^[-*]\s*/, '').replace(/^\d+[.)]\s*/, '').trim())
        .filter(Boolean);
      phases[0].items = fallbackItems.slice(0, 4);
    }

    return phases;
  };

  const getStepOutput = (stepNumber) => {
    const step = steps.find((item) => item.step === stepNumber);
    return step ? step.output : '';
  };

  const getReadinessLabel = (score) => {
    if (score >= 8) return 'Strong fit';
    if (score >= 6) return 'Promising fit';
    if (score > 0) return 'Emerging fit';
    return 'Assessment pending';
  };

  const getExecutiveSnapshot = () => {
    const rankingStep = getStepOutput(4);
    const roadmapStep = normalizeStepOutput(getStepOutput(5));
    const gapStep = getStepOutput(3);

    const rankings = parseRankings(rankingStep);
    const gaps = parseGapLines(gapStep);
    const topCareer = rankings[0];

    const nextAction = roadmapStep
      .split('\n')
      .map((line) => line.replace(/^[-*]\s*/, '').trim())
      .find((line) => line.length > 24 && !line.toLowerCase().includes('step 5 complete'));

    return {
      topCareer: topCareer?.title || 'Career path pending',
      scoreText: topCareer?.scoreText || 'N/A',
      readiness: getReadinessLabel(topCareer?.score || 0),
      priorityGap: gaps[0]?.title || 'Skill deepening',
      nextAction: nextAction || 'Review the roadmap section and choose one action to complete this week.'
    };
  };

  const renderStepContent = (step) => {
    const cleanOutput = normalizeStepOutput(step.output);

    if (step.step === 1) {
      const profileData = parseProfileSummary(step.output);
      return (
        <div className="step-profile-grid">
          <div>
            <h4 className="step-section-title"><span className="emoji">🛠️</span> Current Skills</h4>
            <div className="chip-row">
              {profileData.skills.map((skill) => (
                <span key={skill} className="info-chip">{skill}</span>
              ))}
            </div>
          </div>

          <div>
            <h4 className="step-section-title"><span className="emoji">🎯</span> Career Goal</h4>
            <div className="chip-row">
              {profileData.goals.map((goal) => (
                <span key={goal} className="goal-chip">{goal}</span>
              ))}
            </div>
          </div>

          <div className="step-meta-item">
            <h4 className="step-section-title"><span className="emoji">🎓</span> Education</h4>
            <p>{profileData.education || 'Not specified'}</p>
          </div>

          <div className="step-meta-item">
            <h4 className="step-section-title"><span className="emoji">💼</span> Experience Snapshot</h4>
            <p>{profileData.experience || 'Not specified'}</p>
          </div>
        </div>
      );
    }

    if (step.step === 2) {
      const careers = parseCareerList(step.output);
      return (
        <div>
          <h4 className="step-section-title">Top Matching Career Paths</h4>
          <div className="chip-row">
            {careers.map((career) => (
              <span key={career} className="path-chip">{career}</span>
            ))}
          </div>
        </div>
      );
    }

    if (step.step === 3) {
      const gaps = parseGapLines(step.output);
      return (
        <div className="gap-grid">
          {gaps.length > 0 ? gaps.map((gap) => (
            <article key={gap.title} className="gap-card">
              <h4>{gap.title}</h4>
              <p>{gap.detail}</p>
            </article>
          )) : <p className="step-detail-body">{cleanOutput}</p>}
        </div>
      );
    }

    if (step.step === 4) {
      const rankings = parseRankings(step.output);
      return (
        <div className="ranking-grid">
          {rankings.length > 0 ? rankings.map((rank) => (
            <article key={rank.title} className="ranking-card">
              <div className="ranking-head">
                <h4>{rank.title}</h4>
                <span>{rank.scoreText}</span>
              </div>
              <div className="score-track">
                <div className="score-fill" style={{ width: `${Math.max(0, Math.min(rank.score, 10)) * 10}%` }} />
              </div>
            </article>
          )) : <p className="step-detail-body">{cleanOutput}</p>}
        </div>
      );
    }

    if (step.step === 5) {
      const roadmapPhases = parseRoadmapPhases(step.output);
      return (
        <div className="roadmap-flow">
          <div className="roadmap-track" />
          {roadmapPhases.map((phase, index) => (
            <article key={phase.key} className={`roadmap-card roadmap-card-${phase.key}`}>
              <div className="roadmap-card-head">
                <div>
                  <p className="roadmap-phase-label">{phase.label}</p>
                  <h4>{phase.period}</h4>
                </div>
                <span className="roadmap-badge">{phase.items.length} actions</span>
              </div>

              {phase.items.length > 0 ? (
                <div className="roadmap-items">
                  {phase.items.slice(0, 4).map((item, itemIndex) => (
                    <div key={`${phase.key}-${itemIndex}`} className="roadmap-item">
                      <span className="roadmap-dot" />
                      <p>{item}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="roadmap-empty">The roadmap content will appear here once the step output is parsed.</p>
              )}

              {index < roadmapPhases.length - 1 && <div className="roadmap-arrow">→</div>}
            </article>
          ))}
        </div>
      );
    }

    if (step.step === 6) {
      return (
        <div className="final-plan-markdown">
          <ReactMarkdown>{cleanOutput}</ReactMarkdown>
        </div>
      );
    }

    return <p className="step-detail-body">{cleanOutput}</p>;
  };

  const snapshot = getExecutiveSnapshot();

  return (
    <div className="app">
      <header className="header">
        <h1><span className="emoji">🧭</span> CareerCompass AI</h1>
        <p>AI-Powered Career Guidance through Multi-Step Reasoning</p>
        <span className="badge">Microsoft Azure AI Foundry • GPT-4.1-mini</span>
      </header>

      <div className="main-layout">
        {/* LEFT: INPUT PANEL */}
        <div className="input-panel">
          <h2>Your Profile</h2>
          <textarea
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe Yourself...                                                    
    
Example: I'm a 3rd year CS student. I know Python, React, and basic ML. I've built several begineer level projects like medicine tracker and more. I want to become an AI/ML Engineer."
            rows={8}
            disabled={loading}
          />

          {error && <div className="error">{error}</div>}

          <button
            className={`analyze-btn ${loading ? 'loading' : ''}`}
            onClick={analyzeProfile}
            disabled={loading}
            title={loading ? 'Analyzing...' : 'Click or press Ctrl+Enter'}
          >
            {loading ? '🤔 Analyzing your profile...' : '🚀 Analyze My Career Path'}
          </button>

          {/* REASONING STEPS PROGRESS */}
          {(loading || steps.length > 0) && (
            <div className="steps-panel">
              <h3><span className="emoji">🧠</span> Reasoning Steps</h3>
              {[1, 2, 3, 4, 5, 6].map((stepNum) => (
                <div
                  key={stepNum}
                  className={`step-item ${steps.find(s => s.step === stepNum) ? 'complete' :
                    loading && currentStep >= stepNum ? 'running' : 'pending'
                    }`}
                >
                  <span className="step-icon">
                    {steps.find(s => s.step === stepNum) ? <CheckCircle2 size={18} /> :
                      loading && currentStep >= stepNum ? <Loader2 size={18} className="lucide-spin" /> :
                        <div className="step-pending-circle" />}
                  </span>
                  <span>{STEP_NAMES[stepNum]}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT: RESULTS PANEL */}
        <div className="results-panel">
          {!fullResponse && !loading && (
            <div className="empty-state">
              <div className="empty-icon-container">
                <Target className="empty-icon-svg" size={64} strokeWidth={1.5} />
                <div className="empty-icon-glow"></div>
              </div>
              <h3>Ready for your career analysis?</h3>
              <p>Enter your profile on the left. CareerCompass will analyze your skills through 6 reasoning steps and create a personalized career roadmap.</p>
            </div>
          )}

          {loading && (() => {
            const safeStep = currentStep >= 0 && currentStep <= 6 ? currentStep : 0;
            const currentStepData = LOADING_MESSAGES[safeStep];
            const StepIcon = currentStepData.icon;

            return (
              <div className="loading-state">
                <div className="premium-spinner-container">
                  <div className="premium-spinner-ring"></div>
                  <div className="premium-spinner-ring-inner"></div>
                  <div className="premium-spinner-icon">
                    <StepIcon size={36} strokeWidth={1.5} className="pulse-icon" />
                  </div>
                </div>
                <h3 className="dynamic-loading-text">{currentStepData.text}</h3>
                <div className="loading-progress-bar">
                  <div className="loading-progress-fill" style={{ width: `${(Math.max(1, currentStep) / 6) * 100}%` }}></div>
                </div>
                <p className="loading-subtext">Reasoning step {Math.max(1, currentStep)} of 6</p>
              </div>
            );
          })()}

          {fullResponse && (
            <div className="response-panel analysis-panel">
              <div className="panel-header">
                <div>
                  <span className="panel-kicker">Career Analysis Complete</span>
                  <h2><span className="emoji">📋</span> Your Career Analysis</h2>
                  <p className="panel-description">
                    Review the full reasoning below, then compare paths or refine the recommendation if you want a different direction.
                  </p>
                </div>

                <div className="analysis-badges">
                  <span className="analysis-badge">6-step analysis</span>
                  <span className="analysis-badge">Adaptive feedback</span>
                  <span className="analysis-badge">Career comparison</span>
                </div>
              </div>

              <div className="executive-strip">
                <article className="executive-card executive-card-primary">
                  <p className="executive-label">Best-Fit Path</p>
                  <h3>{snapshot.topCareer}</h3>
                  <p className="executive-note">Current readiness: {snapshot.readiness}</p>
                </article>

                <article className="executive-card">
                  <p className="executive-label">Opportunity Score</p>
                  <h3>{snapshot.scoreText}</h3>
                  <p className="executive-note">Based on match, growth potential, and entry effort.</p>
                </article>

                <article className="executive-card">
                  <p className="executive-label">Priority Gap</p>
                  <h3>{snapshot.priorityGap}</h3>
                  <p className="executive-note">Focus this first to accelerate your transition.</p>
                </article>

                <article className="executive-card executive-card-wide">
                  <p className="executive-label">Next High-Impact Move</p>
                  <h3>{snapshot.nextAction}</h3>
                </article>
              </div>

              <div className="response-text transcript-card">
                {steps.length > 0 ? (
                  <div className="step-detail-list">
                    {steps.map((step) => (
                      <article key={step.step} className="step-detail-card">
                        <h3 className="step-detail-title">{STEP_NAMES[step.step]}</h3>
                        {renderStepContent(step)}
                      </article>
                    ))}
                  </div>
                ) : (
                  fullResponse
                    .split('\n')
                    .map((line) => line.trim())
                    .filter((line) => line.length > 0)
                    .map((line, i) => (
                      <p key={i} className={line.includes('STEP') || line.includes('Step') ? 'step-header' : ''}>
                        {normalizeStepOutput(line)}
                      </p>
                    ))
                )}
              </div>

              <div className="action-stack">
                <section className="action-card demand-card">
                  <div className="action-card-head">
                    <div>
                      <h3>Live Market Demand Intelligence</h3>
                      <p>Public API integration for real demand signals across jobs and open-source activity.</p>
                    </div>
                    <button
                      className="primary-action-btn"
                      onClick={handleAnalyzeMarketDemand}
                      disabled={analyzingDemand}
                    >
                      {analyzingDemand ? 'Analyzing demand...' : 'Analyze Live Market Demand'}
                    </button>
                  </div>

                  {marketDemand && (
                    <div className="demand-results">
                      <div className="demand-summary">
                        <article className="demand-summary-card">
                          <p>Skills analyzed</p>
                          <h4>{marketDemand.analyzed_skills}</h4>
                        </article>
                        <article className="demand-summary-card">
                          <p>Avg demand score</p>
                          <h4>{marketDemand.average_demand_score}/100</h4>
                        </article>
                        <article className="demand-summary-card">
                          <p>Strongest signal</p>
                          <h4>{marketDemand.strongest_market_skill}</h4>
                        </article>
                      </div>

                      <div className="demand-insight-grid">
                        {marketDemand.skill_insights?.map((item) => (
                          <article className="demand-insight-card" key={item.skill}>
                            <div className="demand-insight-head">
                              <h4>{item.skill}</h4>
                              <span className={`demand-band demand-${item.demand_band?.toLowerCase()}`}>{item.demand_band}</span>
                            </div>
                            <p>Demand score: <strong>{item.demand_score}/100</strong></p>
                            <p>Total matching jobs: <strong>{item.himalayas_total_count?.toLocaleString() || 0}</strong></p>
                            <p>Live board matches: {item.job_postings}</p>
                            <p>GitHub repositories: {item.github_repositories?.toLocaleString()}</p>
                            {item.source_breakdown && (
                              <div className="source-breakdown">
                                <p className="source-breakdown-label">Sources:</p>
                                <div className="source-tags">
                                  {Object.entries(item.source_breakdown).map(([src, count]) => (
                                    <span key={src} className={`source-tag ${count > 0 ? 'active' : ''}`}>
                                      {src}: {typeof count === 'number' && count > 999 ? count.toLocaleString() : count}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {item.sample_roles?.length > 0 && (
                              <div className="role-chip-row">
                                {item.sample_roles.map((role) => (
                                  <span key={role} className="role-chip">{role}</span>
                                ))}
                              </div>
                            )}
                          </article>
                        ))}
                      </div>

                      <p className="demand-attribution">
                        Data from Himalayas, RemoteOK, Remotive, Arbeitnow &amp; GitHub &bull; {marketDemand.methodology}
                      </p>
                    </div>
                  )}
                </section>

                <section className="action-card deliverables-card">
                  <div className="action-card-head">
                    <div>
                      <h3>Judge-Ready Deliverables</h3>
                      <p>Download polished artifacts you can demo or attach in your hackathon submission.</p>
                    </div>
                  </div>

                  <div className="deliverables-row">
                    <button
                      className="secondary-action-btn"
                      onClick={handleExportPdf}
                      disabled={exportingPdf}
                    >
                      {exportingPdf ? 'Generating PDF...' : 'Download Career Report (PDF)'}
                    </button>

                    <button
                      className="secondary-action-btn"
                      onClick={handleExportChecklist}
                      disabled={exportingChecklist}
                    >
                      {exportingChecklist ? 'Generating CSV...' : 'Download Skills Checklist (CSV)'}
                    </button>
                  </div>
                </section>

                <section className="action-card">
                  <div className="action-card-head">
                    <div>
                      <h3>Compare Two Careers</h3>
                      <p>Use this when you are choosing between two paths and want a more structured side-by-side view.</p>
                    </div>
                    <button
                      className="secondary-action-btn"
                      onClick={() => setComparisonMode(!comparisonMode)}
                    >
                      {comparisonMode ? 'Hide comparison' : '🔄 Compare Two Careers'}
                    </button>
                  </div>

                  {comparisonMode && (
                    <div className="comparison-panel">
                      <div className="field-stack">
                        <input
                          className="career-input"
                          placeholder="Career 1 (e.g., Machine Learning Engineer)"
                          value={career1}
                          onChange={(e) => setCareer1(e.target.value)}
                        />
                        <input
                          className="career-input"
                          placeholder="Career 2 (e.g., Data Scientist)"
                          value={career2}
                          onChange={(e) => setCareer2(e.target.value)}
                        />
                      </div>

                      <button
                        className="primary-action-btn compare-action-btn"
                        onClick={handleCompare}
                        disabled={comparing || !career1 || !career2}
                      >
                        {comparing ? 'Comparing...' : '⚖️ Compare'}
                      </button>

                      {comparisonResult && (
                        <div className="result-panel comparison-result">
                          <div className="comparison-header">
                            <Trophy className="comparison-header-icon" size={24} />
                            <h4>Detailed Comparison</h4>
                          </div>

                          {comparisonResult.error ? (
                            <p className="error-text">{comparisonResult.error}</p>
                          ) : (
                            <div className="comparison-grid">
                              {/* Career 1 Card */}
                              <div className="career-card">
                                <div className="career-card-header">
                                  <h3>{comparisonResult.career1?.name || career1}</h3>
                                </div>
                                <div className="career-card-body">
                                  <div className="career-attr">
                                    <div className="attr-label"><Clock size={16} /> Time to Enter</div>
                                    <p>{comparisonResult.career1?.time_to_enter}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><TrendingUp size={16} /> Growth Potential</div>
                                    <p>{comparisonResult.career1?.growth_potential}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><Briefcase size={16} /> Job Market</div>
                                    <p>{comparisonResult.career1?.job_market}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><Heart size={16} /> Work-Life Balance</div>
                                    <p>{comparisonResult.career1?.work_life_balance}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><User size={16} /> Best Fit For</div>
                                    <p>{comparisonResult.career1?.best_fit_for}</p>
                                  </div>
                                  <div className="career-attr skills-attr">
                                    <div className="attr-label"><Code size={16} /> Required Skills</div>
                                    <div className="skill-tags">
                                      {comparisonResult.career1?.skills?.map((s, i) => (
                                        <span key={i} className="skill-chip">{s}</span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* VS Badge */}
                              <div className="vs-badge">VS</div>

                              {/* Career 2 Card */}
                              <div className="career-card">
                                <div className="career-card-header">
                                  <h3>{comparisonResult.career2?.name || career2}</h3>
                                </div>
                                <div className="career-card-body">
                                  <div className="career-attr">
                                    <div className="attr-label"><Clock size={16} /> Time to Enter</div>
                                    <p>{comparisonResult.career2?.time_to_enter}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><TrendingUp size={16} /> Growth Potential</div>
                                    <p>{comparisonResult.career2?.growth_potential}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><Briefcase size={16} /> Job Market</div>
                                    <p>{comparisonResult.career2?.job_market}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><Heart size={16} /> Work-Life Balance</div>
                                    <p>{comparisonResult.career2?.work_life_balance}</p>
                                  </div>
                                  <div className="career-attr">
                                    <div className="attr-label"><User size={16} /> Best Fit For</div>
                                    <p>{comparisonResult.career2?.best_fit_for}</p>
                                  </div>
                                  <div className="career-attr skills-attr">
                                    <div className="attr-label"><Code size={16} /> Required Skills</div>
                                    <div className="skill-tags">
                                      {comparisonResult.career2?.skills?.map((s, i) => (
                                        <span key={i} className="skill-chip">{s}</span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {!comparisonResult.error && comparisonResult.recommendation && (
                            <div className="comparison-recommendation">
                              <CheckCircle2 size={20} className="rec-icon" />
                              <p><strong>Verdict:</strong> {comparisonResult.recommendation}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </section>

                {fullResponse && !regenerating && (
                  <section className="action-card">
                    <div className="action-card-head">
                      <div>
                        <h3>Refine the Ranking</h3>
                        <p>Share what you want changed and the agent will re-rank the options around your preferences.</p>
                      </div>
                      <button
                        className="secondary-action-btn"
                        onClick={() => setShowFeedback(!showFeedback)}
                      >
                        {showFeedback ? '✕ Close feedback' : '💭 Give feedback'}
                      </button>
                    </div>

                    {showFeedback && (
                      <div className="feedback-panel">
                        <textarea
                          className="feedback-input"
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                          placeholder="Tell the agent what you'd prefer... (for example: less travel, more research, non-tech options, faster entry)"
                        />
                        <div className="button-row">
                          <button
                            className="primary-action-btn regenerate-btn"
                            onClick={handleRegenerateWithFeedback}
                            disabled={regenerating || !feedback.trim()}
                          >
                            {regenerating ? '🔄 Regenerating...' : '✨ Regenerate Ranking'}
                          </button>
                        </div>
                      </div>
                    )}
                  </section>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        Built for Microsoft Agents League Hackathon 2026 | Azure AI Foundry • GPT-4.1-mini • Azure AI Search
        <br />
        SIES Graduate School of Technology, Navi Mumbai, India
      </footer>
    </div>
  );
}

export default App;