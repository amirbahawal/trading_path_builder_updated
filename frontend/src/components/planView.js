'use client';

import React, { useState, useEffect } from "react";
import { usePlan } from "../hooks/usePlan";
import { logEvent } from "../api/analytics";
import { Lock, CheckCircle, Crown, Sparkles, Target, Zap, TrendingUp, DollarSign, Unlock } from 'lucide-react';

const summaries = [
  {
    icon: TrendingUp,
    title: "Your Trading Psychology Profile",
    text: "Based on your responses, you demonstrate strong analytical thinking with a balanced approach to risk management. Your decision-making style suggests you prefer data-driven strategies over emotional trading. You show patience in waiting for quality setups and have realistic expectations about market volatility. This profile indicates you're well-suited for systematic trading approaches that combine technical analysis with disciplined execution. Your risk tolerance aligns with intermediate strategies that balance growth potential with capital preservation."
  },
  {
    icon: Target,
    title: "Recommended Focus Areas",
    text: "Your current skill level and goals indicate you should prioritize mastering candlestick patterns and support-resistance levels before advancing to complex indicators. Time commitment analysis suggests a swing trading approach would fit your schedule better than day trading. We recommend starting with major currency pairs or large-cap stocks for better liquidity and lower volatility. Focus on developing one core strategy thoroughly before diversifying. Your learning style benefits from practical application, so paper trading with real-time data will accelerate your progress significantly."
  },
  {
    icon: Sparkles,
    title: "Your Growth Trajectory",
    text: "With consistent effort following this path, you can expect to reach basic proficiency within 3-4 months and develop your first profitable strategy within 6-8 months. Your personalized roadmap accounts for your available study time and previous experience. The foundation stage will build essential market knowledge and risk management skills. Strategy development phase introduces advanced concepts and backtesting methodologies. Final automation stage prepares you for scaling operations efficiently. This timeline is realistic and achievable based on similar trader profiles who completed this path successfully."
  }
];

const SplitScreenLayout = ({ isPro, onUnlock, stages }) => {
  const [summaryIndex, setSummaryIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [animateStages, setAnimateStages] = useState(false);
  const [hoveredLocked, setHoveredLocked] = useState(null);

  useEffect(() => {
    if (summaryIndex < summaries.length) {
      const timer = setTimeout(() => {
        if (summaryIndex < summaries.length - 1) {
          setSummaryIndex(summaryIndex + 1);
        } else {
          setTimeout(() => {
            setShowContent(true);
            setTimeout(() => setAnimateStages(true), 300);
          }, 1000);
        }
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [summaryIndex]);

  if (!showContent) {
    const CurrentIcon = summaries[summaryIndex].icon;
    return (
      <div className="w-full h-[calc(100vh-200px)] flex items-center justify-center p-4">
        <div className="max-w-2xl mx-auto bg-zinc-900/60 backdrop-blur-xl border border-violet-500/30 rounded-3xl p-12 shadow-2xl shadow-violet-500/20">
          <div className="flex flex-col items-center text-center">
            <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-violet-600 via-fuchsia-600 to-purple-600 flex items-center justify-center mb-6 animate-pulse">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-violet-600 via-fuchsia-600 to-purple-600 animate-ping opacity-20"></div>
              <CurrentIcon className="w-12 h-12 text-white z-10" />
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-violet-400 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent mb-6">
              {summaries[summaryIndex].title}
            </h2>
            <p className="text-gray-300 text-lg leading-relaxed max-w-3xl">
              {summaries[summaryIndex].text}
            </p>
            <div className="flex gap-2 mt-8">
              {summaries.map((_, i) => (
                <div
                  key={i}
                  className={`h-2 rounded-full transition-all duration-500 ${
                    i === summaryIndex
                      ? 'w-16 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-purple-500'
                      : i < summaryIndex
                      ? 'w-2 bg-violet-600'
                      : 'w-2 bg-zinc-700'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto grid md:grid-cols-2 gap-8">
      {/* LEFT: Sticky Summary + CTA */}
      <div className="space-y-6 md:sticky md:top-8 h-fit">
        {/* Summary Card */}
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-violet-500/30 rounded-3xl p-8 shadow-2xl hover:border-violet-500/50 transition-all">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-violet-100">Your Profile Summary</h2>
          </div>
          <p className="text-gray-300 mb-5">Based on your responses, we've created a personalized 3-stage path tailored to your goals and experience level.</p>
          <ul className="space-y-2 text-gray-300 text-sm">
            {['Personalized learning roadmap', 'Stage-by-stage progression', 'Downloadable resources & guides', 'Progress tracking dashboard'].map((t, i) => (
              <li key={i} className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${i % 3 === 0 ? 'bg-violet-400' : i % 3 === 1 ? 'bg-fuchsia-400' : 'bg-purple-400'}`}></div>
                {t}
              </li>
            ))}
          </ul>
        </div>

        {/* CTA Card */}
        <div className="relative overflow-hidden bg-gradient-to-br from-violet-600 via-fuchsia-600 to-purple-600 rounded-3xl p-6 shadow-2xl">
          <div className="absolute inset-0 bg-grid-white/10"></div>
          <div className="relative text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
              <Crown className="w-8 h-8 text-white animate-bounce" />
            </div>
            <h3 className="text-2xl md:text-3xl font-bold text-white">Unlock Everything</h3>
            <p className="text-violet-100 text-sm md:text-base">Get complete access to all stages with detailed guides, templates, and automation strategies.</p>
            <button 
              onClick={onUnlock} 
              className="w-full py-4 bg-white text-violet-600 rounded-xl font-bold flex items-center justify-center gap-2 hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-violet-500/30"
              style={{
                textShadow: 'none',
                boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3), 0 4px 8px rgba(0, 0, 0, 0.1)',
              }}
            >
              <DollarSign className="w-5 h-5" /> Get Full Access — $5 <Unlock className="w-5 h-5" />
            </button>
            <p className="text-violet-200 text-xs">One-time payment • Lifetime access • All resources</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-violet-500/30 rounded-3xl p-5 shadow-xl">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Your Journey</h4>
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { num: '3', label: 'Stages', grad: 'from-violet-400 to-fuchsia-400' },
              { num: '6-8', label: 'Months', grad: 'from-fuchsia-400 to-purple-400' },
              { num: '15+', label: 'Resources', grad: 'from-purple-400 to-violet-400' }
            ].map((s, i) => (
              <div key={i} className="p-3 bg-white/5 rounded-xl border border-white/10">
                <p className={`text-2xl font-bold bg-gradient-to-r ${s.grad} bg-clip-text text-transparent`}>{s.num}</p>
                <p className="text-xs text-gray-400">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT: Scrollable Stages */}
      <div className="space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)] pr-2">
        <div className="sticky top-0 bg-black/90 backdrop-blur-lg py-3 px-5 rounded-2xl border border-violet-500/20 mb-4 z-10">
          <h3 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-violet-400 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent">
            Your 3-Stage Trading Path
          </h3>
        </div>

        {/* STAGE 1 - UNLOCKED */}
        <div className={`relative bg-zinc-900/80 backdrop-blur-xl border-2 rounded-3xl p-6 shadow-2xl transition-all duration-500 ${animateStages ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-3xl"></div>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-lg">
                <CheckCircle className="w-7 h-7 text-white" />
              </div>
              <div>
                <h4 className="text-2xl font-bold text-green-100">Stage 1: Foundation</h4>
                <p className="text-sm text-gray-400">Build your base knowledge</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-green-600/20 border border-green-500/30 text-green-400 rounded-full text-xs font-bold">
              <CheckCircle className="w-3 h-3" /> Unlocked
            </div>
          </div>
          <p className="text-gray-300 mb-6 text-base leading-relaxed">Master the fundamentals and build a solid foundation for your trading journey with comprehensive lessons.</p>
          <div className="mb-6">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-400">Progress</span>
              <span className="font-bold text-green-400">100% Complete</span>
            </div>
            <div className="h-2.5 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full" style={{ width: '100%' }}></div>
            </div>
          </div>
          <div className="space-y-2">
            {[
              'Market Fundamentals Mastery — Complete understanding of market basics and terminology',
              'Risk Management Excellence — Position sizing and risk-reward principles',
              'First Strategy Development — Build and test your initial trading strategy'
            ].map((item, i) => {
              const [main, sub] = item.split(' — ');
              return (
                <div key={i} className="flex items-start gap-3 p-2.5 rounded-xl bg-green-500/5 border border-green-500/10">
                  <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-gray-200">{main}</p>
                    {sub && <p className="text-xs text-gray-400">{sub}</p>}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex gap-3 mt-6">
            <button className="flex-1 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-xl font-semibold transition-all hover:scale-105 shadow-lg">
              View Resources
            </button>
            <button className="flex-1 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-gray-300 rounded-xl font-semibold border border-zinc-700 transition-all">
              Download PDF
            </button>
          </div>
        </div>

        {/* STAGE 2 - LOCKED */}
        <div
          className={`relative bg-zinc-900/80 backdrop-blur-xl border-2 rounded-3xl transition-all duration-500 ${animateStages ? 'opacity-100 translate-y-0 delay-150' : 'opacity-0 translate-y-8'} hover:border-pink-500/50 hover:shadow-2xl hover:shadow-pink-500/20 cursor-pointer`}
          onMouseEnter={() => setHoveredLocked(2)}
          onMouseLeave={() => setHoveredLocked(null)}
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-pink-500 to-rose-500 rounded-t-3xl"></div>
          <div className={`absolute inset-0 backdrop-blur-xl bg-black/60 z-10 rounded-3xl transition-all ${hoveredLocked === 2 ? 'backdrop-blur-lg bg-black/50' : ''}`}></div>
          <div className={`absolute inset-0 z-20 flex items-center justify-center transition-transform ${hoveredLocked === 2 ? 'scale-110' : 'scale-100'}`}>
            <div className="text-center space-y-3">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center shadow-2xl animate-pulse">
                <Lock className="w-10 h-10 text-white" />
              </div>
              <h4 className="text-xl font-bold text-white">Stage 2 Locked</h4>
              <p className="text-sm text-white/80">Upgrade to unlock advanced strategies</p>
              <button 
                onClick={onUnlock} 
                className="px-6 py-3 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-bold hover:scale-105 shadow-xl hover:shadow-2xl hover:shadow-pink-500/50 transition-all duration-300 text-sm tracking-wide"
                style={{
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
                  boxShadow: '0 8px 24px rgba(236, 72, 153, 0.4), 0 4px 8px rgba(0, 0, 0, 0.2)',
                }}
              >
                Unlock Now — $5
              </button>
            </div>
          </div>
          <div className="p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center shadow-lg">
                  <Target className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-pink-100">Stage 2: Strategy Development</h4>
                  <p className="text-sm text-gray-400">Refine your approach</p>
                </div>
              </div>
            </div>
            <p className="text-gray-300 mb-6 text-base leading-relaxed blur-sm opacity-50">Develop and refine advanced trading strategies with systematic backtesting and optimization frameworks.</p>
            <div className="mb-6">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">Progress</span>
                <span className="font-bold text-pink-400">0% Complete</span>
              </div>
              <div className="h-2.5 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-pink-500 to-rose-500 rounded-full w-0"></div>
              </div>
            </div>
            <div className="space-y-2">
              {(stages && stages.find(s => s.id === 2)?.teaser && stages.find(s => s.id === 2).teaser.length > 0 
                ? stages.find(s => s.id === 2).teaser 
                : [
                'Advanced Technical Analysis — Master complex chart patterns and indicators',
                'Multi-Timeframe Strategies — Develop strategies across multiple timeframes',
                'Backtesting Frameworks — Test and optimize your trading systems',
                'Risk-Reward Optimization — Maximize returns with optimal position sizing'
              ]).map((item, i) => {
                // Handle both format: "Title — Description" and plain text
                const [main, sub] = typeof item === 'string' && item.includes(' — ') 
                  ? item.split(' — ') 
                  : [item, null];
                return (
                  <div key={i} className="flex items-start gap-3 p-2.5 rounded-xl bg-white/5 border border-white/10">
                    <div className="w-5 h-5 border-2 border-white/40 rounded mt-0.5 flex-shrink-0"></div>
                    <div>
                      <p className="font-medium text-gray-200">{main}</p>
                      {sub && <p className="text-xs text-gray-400">{sub}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* STAGE 3 - LOCKED */}
        <div
          className={`relative bg-zinc-900/80 backdrop-blur-xl border-2 rounded-3xl transition-all duration-500 ${animateStages ? 'opacity-100 translate-y-0 delay-300' : 'opacity-0 translate-y-8'} hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/20 cursor-pointer`}
          onMouseEnter={() => setHoveredLocked(3)}
          onMouseLeave={() => setHoveredLocked(null)}
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 via-violet-500 to-fuchsia-500 rounded-t-3xl"></div>
          <div className={`absolute inset-0 backdrop-blur-xl bg-black/60 z-10 rounded-3xl transition-all ${hoveredLocked === 3 ? 'backdrop-blur-lg bg-black/50' : ''}`}></div>
          <div className={`absolute inset-0 z-20 flex items-center justify-center transition-transform ${hoveredLocked === 3 ? 'scale-110' : 'scale-100'}`}>
            <div className="text-center space-y-3">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-2xl animate-pulse">
                <Lock className="w-10 h-10 text-white" />
              </div>
              <h4 className="text-xl font-bold text-white">Stage 3 Locked</h4>
              <p className="text-sm text-white/80">Upgrade to access automation secrets</p>
              <button 
                onClick={onUnlock} 
                className="px-6 py-3 bg-gradient-to-r from-purple-500 via-violet-500 to-fuchsia-500 text-white rounded-xl font-bold hover:scale-105 shadow-xl hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 text-sm tracking-wide"
                style={{
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
                  boxShadow: '0 8px 24px rgba(139, 92, 246, 0.4), 0 4px 8px rgba(0, 0, 0, 0.2)',
                }}
              >
                Unlock Now — $5
              </button>
            </div>
          </div>
          <div className="p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg">
                  <Zap className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-purple-100">Stage 3: Automation & Scale</h4>
                  <p className="text-sm text-gray-400">Scale your operations</p>
                </div>
              </div>
            </div>
            <p className="text-gray-300 mb-6 text-base leading-relaxed blur-sm opacity-50">Scale your trading with portfolio optimization and fully automated trading systems that work 24/7.</p>
            <div className="mb-6">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">Progress</span>
                <span className="font-bold text-purple-400">0% Complete</span>
              </div>
              <div className="h-2.5 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-500 via-violet-500 to-fuchsia-500 rounded-full w-0"></div>
              </div>
            </div>
            <div className="space-y-2">
              {(stages && stages.find(s => s.id === 3)?.teaser && stages.find(s => s.id === 3).teaser.length > 0 
                ? stages.find(s => s.id === 3).teaser 
                : [
                'Algorithm Development — Build sophisticated trading algorithms',
                'Portfolio Optimization — Advanced diversification techniques',
                'Automated Trading Systems — Setup 24/7 automated execution',
                'Performance Analytics — Advanced monitoring and optimization'
              ]).map((item, i) => {
                // Handle both format: "Title — Description" and plain text
                const [main, sub] = typeof item === 'string' && item.includes(' — ') 
                  ? item.split(' — ') 
                  : [item, null];
                return (
                  <div key={i} className="flex items-start gap-3 p-2.5 rounded-xl bg-white/5 border border-white/10">
                    <div className="w-5 h-5 border-2 border-white/40 rounded mt-0.5 flex-shrink-0"></div>
                    <div>
                      <p className="font-medium text-gray-200">{main}</p>
                      {sub && <p className="text-xs text-gray-400">{sub}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function PlanView({ planId, onUnlock, registerPlanRefresh }) {
  const { plan, loading, error, refreshPlan, clearPlan } = usePlan(planId);
  const isPro = plan?.tier === "pro";

  useEffect(() => {
    if (registerPlanRefresh) registerPlanRefresh(refreshPlan, clearPlan);
  }, [registerPlanRefresh, refreshPlan, clearPlan]);

  useEffect(() => {
    if (!plan || !plan.stages) return;
    plan.stages.forEach(stage => {
      if (!isPro && stage.id > 1) {
        // Track preview views for locked stages (free tier users)
        logEvent(`stage${stage.id}_preview_viewed`, { plan_id: planId, stage_id: stage.id, user_id: plan?.user_id || "anon" });
      } else if (isPro && stage.id > 1) {
        // Track actual views for unlocked stages (pro tier users)
        logEvent(`stage${stage.id}_viewed`, { plan_id: planId, stage_id: stage.id, user_id: plan?.user_id || "anon" });
      }
    });
  }, [plan, isPro, planId]);

  const handleUnlockClick = () => {
    logEvent("unlock_click", { plan_id: planId, user_id: plan?.user_id || "anon" });
    onUnlock?.();
  };

  const handleManualRefresh = () => refreshPlan();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading your path...</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black flex items-center justify-center p-4">
        <div className="bg-zinc-900/80 backdrop-blur-xl rounded-2xl p-8 border border-violet-500/30 max-w-md text-center shadow-2xl">
          <h2 className="text-violet-400 text-xl font-bold mb-4">Warning: Unable to Load</h2>
          <p className="text-gray-300 mb-6">{error || "Failed to load your plan."}</p>
          <button onClick={handleManualRefresh} className="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 -right-48 w-96 h-96 bg-fuchsia-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>
      <div className="relative z-10 p-8 pt-24">
        <SplitScreenLayout isPro={isPro} onUnlock={handleUnlockClick} stages={plan?.stages} />
      </div>
      <style jsx>{`
        @keyframes slideDown {
          from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
          to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        .animate-slideDown { animation: slideDown .5s ease-out; }
        .bg-grid-white\\/10 {
          background-image: url("data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 40L40 0L40 40L0 40' fill='none' stroke='white' stroke-width='0.5' opacity='0.1'/%3E%3C/svg%3E");
        }
      `}</style>
    </div>
  );
}