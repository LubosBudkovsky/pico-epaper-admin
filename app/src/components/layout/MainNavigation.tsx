import { Divider, NavLink } from '@mantine/core';
import { useLocation, useNavigate } from 'react-router';
import { useEffect } from 'react';
import Icon from '@/components/Icon';

const navLinks = [
  {
    path: '/',
    label: 'Status',
    icon: 'speedometer',
  },  
  {
    path: '/network/settings',
    label: 'Network',
    icon: 'wifi',
  },
  {
    path: '/epaper/settings',
    label: 'ePaper',
    icon: 'image',
    children: [
      {
        path: '/epaper/settings',
        label: 'Settings',
        icon: 'gear',
      },
      {
        path: '/epaper/context',
        label: 'Context',
        icon: 'cloud-arrow-down',
      }
    ],
  },
  {
    path: '/auth/settings',
    label: 'Security',
    icon: 'lock',
  }  
];

export default function MainNavigation({ close }: { close: () => void }) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    close()
  }, [location])

  return (
    <>
      {navLinks.map(item => {
        return (
          <NavLink
            key={item.label}
            label={item.label}
            variant="filled"
            leftSection={<Icon name={item.icon} />}
            childrenOffset={0}
            active={
              location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(`/${item.path.split('/')[1]}`))
            }
            opened={location.pathname.startsWith(`/${item.path.split('/')[1]}`)}
            onClick={() => navigate(item.path)}
          >

            {item?.children &&
              item.children.map((childItem, childIndex) => {
                return (
                  <div key={childItem.label}>
                    <NavLink
                      label={childItem.label}
                      leftSection={<Icon name={childItem.icon} />}
                      active={location.pathname.startsWith(childItem.path)}
                      onClick={() => navigate(childItem.path)}
                    />
                    {childIndex === item.children.length - 1 && <Divider />}
                  </div>
                );
              })}
          </NavLink>

        );
      })}
    </>
  );
}
