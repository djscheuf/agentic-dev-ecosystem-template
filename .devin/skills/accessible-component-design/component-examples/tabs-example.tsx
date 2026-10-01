import { useState, useRef, useEffect } from 'react';

interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTabId?: string;
}

export function Tabs({ tabs, defaultTabId }: TabsProps) {
  const [selectedIndex, setSelectedIndex] = useState(() => {
    if (defaultTabId) {
      const index = tabs.findIndex(tab => tab.id === defaultTabId);
      return index !== -1 ? index : 0;
    }
    return 0;
  });
  
  const [focusedIndex, setFocusedIndex] = useState(selectedIndex);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    tabRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        nextIndex = (index + 1) % tabs.length;
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        nextIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
      setSelectedIndex(nextIndex);
    }
  };

  return (
    <div className="w-full">
      <div role="tablist" aria-label="Content sections" className="flex border-b border-gray-200">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => (tabRefs.current[index] = el)}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={index === selectedIndex}
            aria-controls={`panel-${tab.id}`}
            tabIndex={index === focusedIndex ? 0 : -1}
            onClick={() => {
              setSelectedIndex(index);
              setFocusedIndex(index);
            }}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={`px-4 py-2 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset ${
              index === selectedIndex
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab, index) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={index !== selectedIndex}
          tabIndex={0}
          className="p-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}

export function TabsExample() {
  const tabs: Tab[] = [
    {
      id: 'profile',
      label: 'Profile',
      content: (
        <div>
          <h3 className="text-lg font-semibold mb-2">Profile Settings</h3>
          <p className="text-gray-700 mb-4">
            Manage your profile information and preferences.
          </p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
            Edit Profile
          </button>
        </div>
      ),
    },
    {
      id: 'security',
      label: 'Security',
      content: (
        <div>
          <h3 className="text-lg font-semibold mb-2">Security Settings</h3>
          <p className="text-gray-700 mb-4">
            Update your password and security preferences.
          </p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
            Change Password
          </button>
        </div>
      ),
    },
    {
      id: 'notifications',
      label: 'Notifications',
      content: (
        <div>
          <h3 className="text-lg font-semibold mb-2">Notification Settings</h3>
          <p className="text-gray-700 mb-4">
            Configure how and when you receive notifications.
          </p>
          <label className="flex items-center mb-2">
            <input type="checkbox" className="mr-2" />
            Email notifications
          </label>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" />
            Push notifications
          </label>
        </div>
      ),
    },
  ];

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Account Settings</h2>
      <Tabs tabs={tabs} defaultTabId="profile" />
    </div>
  );
}
