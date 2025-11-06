import React from "react";

/**
 * Teaser component
 * Displays a short list of bullet points or a preview snippet
 * used for locked stages (Stages 2 and 3)
 *
 * Props:
 * - items: array of teaser strings
 * - title: optional title to display above bullets
 */
const Teaser = ({ title = "Coming up next", items = [] }) => {
  return (
    <div className="bg-gray-50 border rounded-xl p-4 mt-3">
      <h4 className="text-gray-800 font-semibold mb-2">{title}</h4>
      <ul className="list-disc list-inside text-gray-600 space-y-1">
        {items.map((item, idx) => (
          <li key={idx} className="text-sm">
            {item}
          </li>
        ))}
      </ul>
      <p className="text-xs text-gray-500 mt-3 italic">
        Unlock this stage to reveal your personalized plan.
      </p>
    </div>
  );
};

export default Teaser;
