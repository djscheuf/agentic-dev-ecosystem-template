import { useState } from 'react';

interface FormData {
  name: string;
  email: string;
  role: string;
  newsletter: boolean;
}

interface FormErrors {
  name?: string;
  email?: string;
  role?: string;
}

export function AccessibleFormExample() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    role: '',
    newsletter: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.role) {
      newErrors.role = 'Please select a role';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    await new Promise(resolve => setTimeout(resolve, 1000));

    setIsSubmitting(false);
    setSubmitSuccess(true);
    
    setFormData({
      name: '',
      email: '',
      role: '',
      newsletter: false,
    });
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">User Registration</h1>

      {submitSuccess && (
        <div
          role="alert"
          className="mb-6 p-4 bg-green-50 border border-green-200 rounded"
        >
          <p className="text-green-800">Registration successful!</p>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-4">
          <label 
            htmlFor="name" 
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Name <span className="text-red-600" aria-label="required">*</span>
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            aria-required="true"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'name-error' : undefined}
            className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.name && (
            <div id="name-error" role="alert" className="mt-1 text-sm text-red-600">
              {errors.name}
            </div>
          )}
        </div>

        <div className="mb-4">
          <label 
            htmlFor="email" 
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Email <span className="text-red-600" aria-label="required">*</span>
          </label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
            aria-required="true"
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? 'email-error' : undefined}
            className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.email ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.email && (
            <div id="email-error" role="alert" className="mt-1 text-sm text-red-600">
              {errors.email}
            </div>
          )}
        </div>

        <fieldset className="mb-4">
          <legend className="block text-sm font-medium text-gray-700 mb-2">
            Role <span className="text-red-600" aria-label="required">*</span>
          </legend>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                name="role"
                value="developer"
                checked={formData.role === 'developer'}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                aria-invalid={!!errors.role}
                className="mr-2 focus:ring-2 focus:ring-blue-500"
              />
              Developer
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="role"
                value="designer"
                checked={formData.role === 'designer'}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                aria-invalid={!!errors.role}
                className="mr-2 focus:ring-2 focus:ring-blue-500"
              />
              Designer
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="role"
                value="manager"
                checked={formData.role === 'manager'}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                aria-invalid={!!errors.role}
                className="mr-2 focus:ring-2 focus:ring-blue-500"
              />
              Manager
            </label>
          </div>
          {errors.role && (
            <div id="role-error" role="alert" className="mt-1 text-sm text-red-600">
              {errors.role}
            </div>
          )}
        </fieldset>

        <div className="mb-6">
          <label className="flex items-start">
            <input
              type="checkbox"
              checked={formData.newsletter}
              onChange={(e) => setFormData({ ...formData, newsletter: e.target.checked })}
              className="mt-1 mr-2 focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">
              Subscribe to newsletter for updates and announcements
            </span>
          </label>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </button>
          <button
            type="button"
            onClick={() => {
              setFormData({ name: '', email: '', role: '', newsletter: false });
              setErrors({});
              setSubmitSuccess(false);
            }}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
}
