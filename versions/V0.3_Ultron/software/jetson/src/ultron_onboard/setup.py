from setuptools import setup

package_name = 'ultron_onboard'

setup(
    name=package_name,
    version='0.3.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sadnan Sajid355',
    maintainer_email='sadnan.sajid355@example.com',
    description='Ultron_V0.3 onboard nodes: Kinect driver, depth-to-scan, safety, serial bridge, data logger.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'kinect_driver_node = ultron_onboard.kinect_driver_node:main',
            'depth_to_scan_node = ultron_onboard.depth_to_scan_node:main',
            'safety_node = ultron_onboard.safety_node:main',
            'serial_node = ultron_onboard.serial_node:main',
            'data_logger_node = ultron_onboard.data_logger_node:main',
        ],
    },
)
