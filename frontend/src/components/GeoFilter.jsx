export default function GeoFilter({ filter, onChange }) {
  const update = (field, value) => {
    onChange({ ...filter, [field]: value || null });
  };

  return (
    <div className="flex flex-wrap gap-3">
      {["country", "state", "city", "university"].map((field) => (
        <input
          key={field}
          type="text"
          placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
          value={filter[field] || ""}
          onChange={(e) => update(field, e.target.value)}
          className="px-3 py-2 bg-dark-card border border-dark-border rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors w-36"
        />
      ))}
    </div>
  );
}
