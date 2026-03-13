/**
 * Hook para verificação de privilégios de Super Admin
 */

import React from 'react';
import { useAuth, SUPER_ADMIN_EMAILS, SUPER_ADMIN_USERNAMES } from '../utils/authUtils';

export const useIsSuperAdmin = (): boolean => {
  const { user } = useAuth();
  
  return React.useMemo(() => {
    if (!user) return false;
    
    return user.is_super_admin === true || 
           (user.role === 'ADMIN' && 
            (SUPER_ADMIN_EMAILS.includes(user.email) || 
             SUPER_ADMIN_USERNAMES.includes(user.username)));
  }, [user]);
};
