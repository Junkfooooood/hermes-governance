import { useState } from "react";

interface SearchBarProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  className?: string;
}

export default function SearchBar({
  placeholder = "搜索...",
  onSearch,
  className = "",
}: SearchBarProps) {
  const [value, setValue] = useState("");

  return (
    <input
      type="text"
      value={value}
      onChange={(e) => {
        setValue(e.target.value);
        onSearch(e.target.value);
      }}
      placeholder={placeholder}
      className={`w-full px-3 py-1.5 text-sm border border-gray-200 rounded-md
        focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300
        placeholder:text-gray-300 ${className}`}
    />
  );
}
