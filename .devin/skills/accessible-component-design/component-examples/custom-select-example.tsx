import { useState, useRef, useEffect } from 'react';

interface Option {
  id: string;
  label: string;
  value: string;
}

interface CustomSelectProps {
  label: string;
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function CustomSelect({ label, options, value, onChange, placeholder = 'Select an option' }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const optionRefs = useRef<(HTMLLIElement | null)[]>([]);

  const selectedOption = options.find(opt => opt.value === value);

  useEffect(() => {
    if (isOpen && focusedIndex >= 0) {
      optionRefs.current[focusedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [focusedIndex, isOpen]);

  const handleButtonKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowUp':
        e.preventDefault();
        setIsOpen(true);
        setFocusedIndex(value ? options.findIndex(opt => opt.value === value) : 0);
        break;
      case ' ':
      case 'Enter':
        e.preventDefault();
        setIsOpen(!isOpen);
        if (!isOpen) {
          setFocusedIndex(value ? options.findIndex(opt => opt.value === value) : 0);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
      default:
        handleTypeAhead(e.key);
    }
  };

  const handleListKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex((prev) => (prev + 1) % options.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex((prev) => (prev - 1 + options.length) % options.length);
        break;
      case 'Home':
        e.preventDefault();
        setFocusedIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setFocusedIndex(options.length - 1);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (focusedIndex >= 0) {
          onChange(options[focusedIndex].value);
          setIsOpen(false);
          buttonRef.current?.focus();
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        buttonRef.current?.focus();
        break;
      default:
        handleTypeAhead(e.key);
    }
  };

  const handleTypeAhead = (key: string) => {
    if (key.length !== 1) return;

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    const newQuery = searchQuery + key.toLowerCase();
    setSearchQuery(newQuery);

    const matchIndex = options.findIndex(opt =>
      opt.label.toLowerCase().startsWith(newQuery)
    );

    if (matchIndex !== -1) {
      setFocusedIndex(matchIndex);
      if (!isOpen) {
        onChange(options[matchIndex].value);
      }
    }

    setSearchTimeout(
      setTimeout(() => {
        setSearchQuery('');
      }, 500)
    );
  };

  const handleClickOutside = (e: MouseEvent) => {
    if (
      buttonRef.current &&
      listboxRef.current &&
      !buttonRef.current.contains(e.target as Node) &&
      !listboxRef.current.contains(e.target as Node)
    ) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  return (
    <div className="relative">
      <label id="select-label" className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby="select-label"
        aria-controls="select-listbox"
        onKeyDown={handleButtonKeyDown}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between"
      >
        <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <ul
          ref={listboxRef}
          id="select-listbox"
          role="listbox"
          aria-labelledby="select-label"
          tabIndex={-1}
          onKeyDown={handleListKeyDown}
          className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-auto focus:outline-none"
        >
          {options.map((option, index) => (
            <li
              key={option.id}
              ref={(el) => (optionRefs.current[index] = el)}
              role="option"
              aria-selected={option.value === value}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
                buttonRef.current?.focus();
              }}
              className={`px-3 py-2 cursor-pointer ${
                index === focusedIndex ? 'bg-blue-100' : ''
              } ${
                option.value === value ? 'bg-blue-50 font-medium' : ''
              } hover:bg-blue-50`}
            >
              {option.label}
              {option.value === value && (
                <svg className="inline-block w-5 h-5 ml-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function CustomSelectExample() {
  const [selectedCountry, setSelectedCountry] = useState('');

  const countries: Option[] = [
    { id: '1', label: 'United States', value: 'us' },
    { id: '2', label: 'Canada', value: 'ca' },
    { id: '3', label: 'United Kingdom', value: 'uk' },
    { id: '4', label: 'Germany', value: 'de' },
    { id: '5', label: 'France', value: 'fr' },
    { id: '6', label: 'Japan', value: 'jp' },
    { id: '7', label: 'Australia', value: 'au' },
  ];

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Custom Select Example</h2>
      
      <CustomSelect
        label="Country"
        options={countries}
        value={selectedCountry}
        onChange={setSelectedCountry}
        placeholder="Select a country"
      />

      {selectedCountry && (
        <div className="mt-4 p-4 bg-blue-50 rounded">
          <p className="text-sm text-gray-700">
            Selected: <strong>{countries.find(c => c.value === selectedCountry)?.label}</strong>
          </p>
        </div>
      )}

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <p className="text-sm text-gray-700">
          <strong>Note:</strong> Consider using native <code className="bg-white px-1 rounded">&lt;select&gt;</code> 
          or ShadCN/Radix Select component instead of custom implementation when possible.
        </p>
      </div>
    </div>
  );
}
