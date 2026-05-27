import { useState } from 'react';
import { UPCOMING_FEATURES, CATEGORY_COLORS, STATUS_LABELS, type FeatureCategory } from './upcomingFeatures';

export default function UpcomingPage() {
  const [activeCategory, setActiveCategory] = useState<FeatureCategory | 'All'>('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredFeatures = activeCategory === 'All'
    ? UPCOMING_FEATURES
    : UPCOMING_FEATURES.filter(f => f.category === activeCategory);

  const categories: Array<FeatureCategory | 'All'> = [
    'All',
    'AI Intelligence',
    'Production & Scale',
    'Analytics Depth',
    'Social Media Intelligence'
  ];

  const handleCategoryClick = (category: FeatureCategory | 'All') => {
    if (activeCategory === category && category !== 'All') {
      setActiveCategory('All');
    } else {
      setActiveCategory(category);
    }
  };

  const handleCardClick = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-serif text-4xl font-bold text-ink dark:text-stone-100 mb-3">
          Upcoming Features
        </h1>
        <p className="text-stone-600 dark:text-stone-400 text-lg">
          Everything being built next for ClubOS — organized by category, explained in plain English.
        </p>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap gap-2 mb-8">
        {categories.map((category) => {
          const isActive = activeCategory === category;
          const isAll = category === 'All';

          const colors = !isAll ? CATEGORY_COLORS[category as FeatureCategory] : null;

          return (
            <button
              key={category}
              onClick={() => handleCategoryClick(category)}
              className={`
                px-4 py-2 rounded-full text-sm font-sans font-medium transition-all
                ${isActive
                  ? isAll
                    ? 'bg-stone-800 dark:bg-stone-200 text-white dark:text-stone-900'
                    : `${colors?.bg} ${colors?.text} ${colors?.border} border-2`
                  : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 hover:bg-stone-200 dark:hover:bg-stone-700'
                }
              `}
            >
              {category}
            </button>
          );
        })}
      </div>

      {/* Feature Cards */}
      <div className="space-y-4">
        {filteredFeatures.map((feature) => {
          const isExpanded = expandedId === feature.id;
          const colors = CATEGORY_COLORS[feature.category];
          const status = STATUS_LABELS[feature.status];

          return (
            <div
              key={feature.id}
              className={`
                border-2 rounded-lg overflow-hidden transition-all
                ${colors.border}
                ${isExpanded ? colors.bg : 'bg-white dark:bg-stone-900'}
                hover:shadow-md cursor-pointer
              `}
              onClick={() => handleCardClick(feature.id)}
            >
              {/* Card Header - Always Visible */}
              <div className="p-6">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <h3 className="font-serif text-xl font-bold text-ink dark:text-stone-100 mb-1">
                      {feature.name}
                    </h3>
                    <div className="flex items-center gap-3 text-sm">
                      <span className={`flex items-center gap-1.5 ${colors.text}`}>
                        <span className={`w-2 h-2 rounded-full ${colors.dot}`}></span>
                        {feature.category}
                      </span>
                      <span className={`${status.color} font-medium`}>
                        {status.label}
                      </span>
                    </div>
                  </div>
                  <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                    <svg className="w-6 h-6 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                <p className="text-stone-700 dark:text-stone-300 leading-relaxed">
                  {feature.tagline}
                </p>
              </div>

              {/* Expanded Content - Conditional */}
              {isExpanded && (
                <div className="px-6 pb-6 space-y-4 animate-fade-in">
                  <div className="pt-4 border-t border-stone-200 dark:border-stone-700">
                    <h4 className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                      What it is
                    </h4>
                    <p className="text-stone-700 dark:text-stone-300 leading-relaxed">
                      {feature.whatItIs}
                    </p>
                  </div>

                  <div>
                    <h4 className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                      What it adds
                    </h4>
                    <p className="text-stone-700 dark:text-stone-300 leading-relaxed">
                      {feature.whatItAdds}
                    </p>
                  </div>

                  <div>
                    <h4 className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                      What it enables
                    </h4>
                    <p className="text-stone-700 dark:text-stone-300 leading-relaxed">
                      {feature.whatItEnables}
                    </p>
                  </div>

                  <div className={`p-4 rounded-lg ${colors.bg}`}>
                    <h4 className={`font-mono text-xs uppercase tracking-widest ${colors.text} mb-2`}>
                      How it will be built
                    </h4>
                    <p className={`${colors.text} leading-relaxed`}>
                      {feature.howItWillBeBuilt}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Count */}
      <div className="mt-8 text-center text-sm text-stone-500 dark:text-stone-400">
        Showing {filteredFeatures.length} of {UPCOMING_FEATURES.length} features
        {activeCategory !== 'All' && ` in ${activeCategory}`}
      </div>
    </div>
  );
}
