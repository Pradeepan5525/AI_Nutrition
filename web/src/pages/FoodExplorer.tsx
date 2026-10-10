import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  X,
  ChevronLeft,
  ChevronRight,
  Columns,
  CheckCircle,
  HelpCircle,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const FoodExplorer: React.FC = () => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [minHealthScore, setMinHealthScore] = useState<number>(0);
  const [excludeAllergens, setExcludeAllergens] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);

  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [totalMatches, setTotalMatches] = useState(0);

  // Detail Drawer state
  const [selectedFood, setSelectedFood] = useState<any | null>(null);
  const [swaps, setSwaps] = useState<any[]>([]);
  const [loadingSwaps, setLoadingSwaps] = useState(false);

  // Comparison state (up to 3 foods)
  const [compareList, setCompareList] = useState<any[]>([]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);

  const availableAllergens = ['gluten', 'dairy', 'nuts', 'peanuts', 'soy', 'eggs', 'fish'];

  useEffect(() => {
    fetchFoods();
  }, [category, minHealthScore, excludeAllergens, page]);

  const fetchFoods = async () => {
    setIsLoading(true);
    try {
      const res = await api.foods.search({
        q: query,
        category: category || undefined,
        min_health_score: minHealthScore > 0 ? minHealthScore : undefined,
        exclude_allergens: excludeAllergens.length > 0 ? excludeAllergens : undefined,
        page,
        page_size: pageSize,
      });
      setResults(res.results || []);
      setTotalMatches(res.total_matches || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchFoods();
  };

  const handleRowClick = async (food: any) => {
    setSelectedFood(food);
    setLoadingSwaps(true);
    try {
      const swapRes = await api.foods.getSwaps(food.food_id, 3, true);
      setSwaps(swapRes.swaps || []);
    } catch {
      setSwaps([]);
    } finally {
      setLoadingSwaps(false);
    }
  };

  const toggleAllergen = (allg: string) => {
    if (excludeAllergens.includes(allg)) {
      setExcludeAllergens(excludeAllergens.filter((a) => a !== allg));
    } else {
      setExcludeAllergens([...excludeAllergens, allg]);
    }
    setPage(1);
  };

  const toggleCompare = (food: any) => {
    if (compareList.some((f) => f.food_id === food.food_id)) {
      setCompareList(compareList.filter((f) => f.food_id !== food.food_id));
    } else {
      if (compareList.length >= 3) {
        alert('You can compare a maximum of 3 foods at once.');
        return;
      }
      setCompareList([...compareList, food]);
    }
  };

  const totalPages = Math.ceil(totalMatches / pageSize);

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Module 04</Badge>
          <Badge variant="neutral">USDA &amp; OpenFoodFacts Repository</Badge>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-text">Food Intelligence Explorer</h1>
            <p className="text-xs sm:text-sm text-muted mt-1">
              Search over 30,000 verified nutritional items with Health Score v2 transparent ranking and
              tri-state allergen screening.
            </p>
          </div>
          {compareList.length > 0 && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setCompareModalOpen(true)}
              leftIcon={<Columns className="w-4 h-4" />}
            >
              Compare ({compareList.length}/3)
            </Button>
          )}
        </div>
      </Card>

      {/* Filter Card */}
      <Card className="p-5">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            {/* Search Input */}
            <div className="md:col-span-6 relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search food item (e.g. Salmon, Oats, Spinach, Greek Yogurt)..."
                className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              />
              <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            </div>

            {/* Category Dropdown */}
            <div className="md:col-span-4">
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              >
                <option value="">All Categories</option>
                <option value="Vegetables">Vegetables &amp; Greens</option>
                <option value="Fruits">Fruits &amp; Berries</option>
                <option value="Proteins">Fish, Poultry &amp; Meat</option>
                <option value="Grains">Whole Grains &amp; Cereals</option>
                <option value="Dairy">Dairy &amp; Alternatives</option>
                <option value="Legumes">Beans, Peas &amp; Legumes</option>
                <option value="Snacks">Nuts, Seeds &amp; Snacks</option>
              </select>
            </div>

            {/* Search Button */}
            <div className="md:col-span-2">
              <Button type="submit" variant="primary" size="md" className="w-full h-full py-2.5">
                Search
              </Button>
            </div>
          </div>

          {/* Allergen Exclusion Chips */}
          <div className="pt-2 border-t border-border/60">
            <span className="text-[11px] font-bold text-muted uppercase tracking-wider block mb-2">
              Exclude Allergens (Tri-State Safe):
            </span>
            <div className="flex flex-wrap gap-2">
              {availableAllergens.map((a) => {
                const isExcluded = excludeAllergens.includes(a);
                return (
                  <button
                    key={a}
                    type="button"
                    onClick={() => toggleAllergen(a)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold capitalize border transition-all ${
                      isExcluded
                        ? 'bg-danger text-white border-danger'
                        : 'bg-surface text-muted border-border hover:bg-bg'
                    }`}
                  >
                    {isExcluded ? `\u2715 Excluded: ${a}` : `+ ${a}`}
                  </button>
                );
              })}
            </div>
          </div>
        </form>
      </Card>

      {/* Results Table */}
      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-muted">
            Matching Catalog Items ({totalMatches})
          </span>
          <span className="text-xs text-muted">
            Page {page} of {totalPages || 1}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-bg text-[11px] font-bold text-muted uppercase tracking-wider border-b border-border">
                <th className="py-3 px-4">Food Item</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Calories (100g)</th>
                <th className="py-3 px-4">Protein</th>
                <th className="py-3 px-4">Carbs</th>
                <th className="py-3 px-4">Fat</th>
                <th className="py-3 px-4">Sodium</th>
                <th className="py-3 px-4">Health Score v2</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-xs text-text">
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-muted">
                    Searching catalog repository...
                  </td>
                </tr>
              ) : results.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-muted">
                    No matching food items found. Try relaxing allergen or query terms.
                  </td>
                </tr>
              ) : (
                results.map((f) => {
                  const isCompared = compareList.some((c) => c.food_id === f.food_id);
                  return (
                    <tr
                      key={f.food_id}
                      className="hover:bg-bg/80 transition-colors cursor-pointer"
                      onClick={() => handleRowClick(f)}
                    >
                      <td className="py-3 px-4 font-semibold text-text max-w-xs truncate">
                        {f.name}
                      </td>
                      <td className="py-3 px-4 text-muted">{f.category}</td>
                      <td className="py-3 px-4 font-semibold">{f.kcal_100g} kcal</td>
                      <td className="py-3 px-4">{f.protein_100g}g</td>
                      <td className="py-3 px-4">{f.carbs_100g}g</td>
                      <td className="py-3 px-4">{f.fat_100g}g</td>
                      <td className="py-3 px-4">{f.sodium_mg_100g}mg</td>
                      <td className="py-3 px-4">
                        <Badge variant={f.health_score_v2 >= 70 ? 'success' : 'neutral'}>
                          {f.health_score_v2} / 100
                        </Badge>
                      </td>
                      <td
                        className="py-3 px-4 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => toggleCompare(f)}
                          className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                            isCompared
                              ? 'bg-primary text-white border-primary'
                              : 'bg-surface text-muted border-border hover:bg-bg'
                          }`}
                        >
                          {isCompared ? 'Compared' : '+ Compare'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-5 py-3 border-t border-border flex items-center justify-between text-xs text-muted">
          <span>
            Showing {results.length} of {totalMatches} items
          </span>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Slide-over Side Drawer for Selected Food Details */}
      {selectedFood && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div
            className="absolute inset-0 bg-text/20 backdrop-blur-xs transition-opacity"
            onClick={() => setSelectedFood(null)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-surface border-l border-border shadow-2xl p-6 overflow-y-auto space-y-5">
              <div className="flex items-start justify-between pb-4 border-b border-border">
                <div>
                  <Badge variant="accent" className="mb-1">
                    {selectedFood.category}
                  </Badge>
                  <h3 className="text-lg font-bold text-text leading-snug">
                    {selectedFood.name}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedFood(null)}
                  className="p-1 rounded-lg text-muted hover:text-text hover:bg-bg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Health Score Banner */}
              <div className="p-4 rounded-xl bg-primary-soft border border-primary/20 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-primary uppercase block">
                    Health Score v2
                  </span>
                  <span className="text-2xl font-extrabold text-primary">
                    {selectedFood.health_score_v2}
                    <span className="text-xs font-normal text-muted ml-1">/ 100</span>
                  </span>
                </div>
                <Badge variant="success">Evidence-Ranked</Badge>
              </div>

              {/* Nutrients Breakdown per 100g */}
              <div>
                <h4 className="text-xs font-bold text-muted uppercase tracking-wider mb-2.5">
                  Nutritional Composition (per 100g)
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Calories</span>
                    <span className="font-bold text-text">{selectedFood.kcal_100g} kcal</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Protein</span>
                    <span className="font-bold text-text">{selectedFood.protein_100g}g</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Carbohydrates</span>
                    <span className="font-bold text-text">{selectedFood.carbs_100g}g</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Total Fat</span>
                    <span className="font-bold text-text">{selectedFood.fat_100g}g</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Dietary Fiber</span>
                    <span className="font-bold text-text">{selectedFood.fiber_100g}g</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block text-[10px]">Sodium</span>
                    <span className="font-bold text-text">{selectedFood.sodium_mg_100g}mg</span>
                  </div>
                </div>
              </div>

              {/* Tri-State Allergen Status (present / absent / UNKNOWN) */}
              <div>
                <h4 className="text-xs font-bold text-muted uppercase tracking-wider mb-2.5 flex items-center">
                  <ShieldAlert className="w-3.5 h-3.5 mr-1 text-primary" />
                  Tri-State Allergen Disclosures
                </h4>
                <div className="space-y-1.5 text-xs">
                  {Object.entries(selectedFood.allergens || {}).map(([alg, status]: [string, any]) => {
                    let badgeVariant: any = 'neutral';
                    let label = 'Unknown (Treated as Excluded)';
                    if (status === 'present') {
                      badgeVariant = 'danger';
                      label = 'Contains Allergen';
                    } else if (status === 'absent') {
                      badgeVariant = 'success';
                      label = 'Verified Allergen-Free';
                    }

                    return (
                      <div
                        key={alg}
                        className="p-2 rounded-lg bg-bg border border-border flex items-center justify-between"
                      >
                        <span className="capitalize font-medium text-text">{alg}</span>
                        <Badge variant={badgeVariant}>{label}</Badge>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Healthier Same-Category Swaps */}
              <div>
                <h4 className="text-xs font-bold text-muted uppercase tracking-wider mb-2.5 flex items-center">
                  <Sparkles className="w-3.5 h-3.5 mr-1 text-primary-accent" />
                  Healthier Same-Category Swaps
                </h4>
                {loadingSwaps ? (
                  <p className="text-xs text-muted">Searching for verified alternatives...</p>
                ) : swaps.length === 0 ? (
                  <p className="text-xs text-muted">
                    This item is already among the highest scoring in its category.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {swaps.map((s) => (
                      <div
                        key={s.food_id}
                        className="p-3 rounded-xl border border-border bg-bg hover:border-primary text-xs transition-colors"
                      >
                        <div className="flex items-center justify-between font-semibold text-text">
                          <span>{s.name}</span>
                          <span className="text-primary font-bold">
                            Score: {s.health_score_v2}/100
                          </span>
                        </div>
                        <span className="text-[11px] text-muted block mt-1">
                          +{s.score_improvement} pts improvement &bull; {s.reasons?.join(', ')}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3-Way Food Comparison Modal */}
      <Modal
        isOpen={compareModalOpen}
        onClose={() => setCompareModalOpen(false)}
        title="Side-by-Side Nutritional Comparison"
        maxWidth="max-w-3xl"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-bg">
                <th className="py-2.5 px-3 font-bold text-muted uppercase">Metric</th>
                {compareList.map((f) => (
                  <th key={f.food_id} className="py-2.5 px-3 font-bold text-text">
                    {f.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Category</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3">
                    {f.category}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Health Score v2</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3 font-bold text-primary">
                    {f.health_score_v2} / 100
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Calories (100g)</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3">
                    {f.kcal_100g} kcal
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Protein (100g)</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3 font-semibold">
                    {f.protein_100g}g
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Carbohydrates (100g)</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3">
                    {f.carbs_100g}g
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Fat (100g)</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3">
                    {f.fat_100g}g
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-muted">Sodium (100g)</td>
                {compareList.map((f) => (
                  <td key={f.food_id} className="py-2.5 px-3">
                    {f.sodium_mg_100g}mg
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </Modal>

      <DisclaimerNotice />
    </div>
  );
};
