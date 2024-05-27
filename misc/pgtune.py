import os
from math import ceil, floor

# postgresql versions
DEFAULT_DB_VERSION = 16
DB_VERSIONS = [DEFAULT_DB_VERSION, 15, 14, 13, 12, 11, 10]

# os types
OS_LINUX = 'linux'
OS_WINDOWS = 'windows'
OS_MAC = 'mac'

# db types
DB_TYPE_WEB = 'web'
DB_TYPE_OLTP = 'oltp'
DB_TYPE_DW = 'dw'
DB_TYPE_DESKTOP = 'desktop'
DB_TYPE_MIXED = 'mixed'

# size units
SIZE_UNIT_MB = 'MB'
SIZE_UNIT_GB = 'GB'

# harddrive types
HARD_DRIVE_SSD = 'ssd'
HARD_DRIVE_SAN = 'san'
HARD_DRIVE_HDD = 'hdd'

SIZE_UNIT_MAP = {
    'KB': 1024,
    'MB': 1048576,
    'GB': 1073741824,
    'TB': 1099511627776
}

DEFAULT_DB_SETTINGS = {
    'default': {
        'max_worker_processes': 8,
        'max_parallel_workers_per_gather': 2,
        'max_parallel_workers': 8
    }
}

# utils
def get_cpu_and_memory():
    cpu_num = os.cpu_count()
    total_memory = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    mem_gb = total_memory // SIZE_UNIT_MAP['GB']
    return cpu_num, mem_gb

# main
def pgtune(config={}, log=True):
    db_version = config.get('db_version', DEFAULT_DB_VERSION)
    os_type = config.get('os_type', OS_LINUX)
    db_type = config.get('db_type', DB_TYPE_WEB)
    cpu_num, total_memory = get_cpu_and_memory()
    # total_memory = config.get('total_memory')
    total_memory_unit = config.get('total_memory_unit', SIZE_UNIT_GB)
    # cpu_num = config.get('cpu_num')
    connection_num = config.get('connection_num')
    hd_type = config.get('hd_type', HARD_DRIVE_SSD)

    total_memory_bytes = total_memory * SIZE_UNIT_MAP[total_memory_unit]
    total_memory_kb = total_memory_bytes // SIZE_UNIT_MAP['KB']

    db_default_values = DEFAULT_DB_SETTINGS.get(db_version, DEFAULT_DB_SETTINGS['default'])

    max_connections = connection_num if connection_num else {
        DB_TYPE_WEB: 200,
        DB_TYPE_OLTP: 300,
        DB_TYPE_DW: 40,
        DB_TYPE_DESKTOP: 20,
        DB_TYPE_MIXED: 100
    }[db_type]

    huge_pages = 'try' if total_memory_kb >= 33554432 else 'off'

    shared_buffers = {
        DB_TYPE_WEB: total_memory_kb // 4,
        DB_TYPE_OLTP: total_memory_kb // 4,
        DB_TYPE_DW: total_memory_kb // 4,
        DB_TYPE_DESKTOP: total_memory_kb // 16,
        DB_TYPE_MIXED: total_memory_kb // 4
    }[db_type]

    if db_version < 10 and os_type == OS_WINDOWS:
        win_memory_limit = (512 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
        if shared_buffers > win_memory_limit:
            shared_buffers = win_memory_limit

    effective_cache_size = {
        DB_TYPE_WEB: (total_memory_kb * 3) // 4,
        DB_TYPE_OLTP: (total_memory_kb * 3) // 4,
        DB_TYPE_DW: (total_memory_kb * 3) // 4,
        DB_TYPE_DESKTOP: total_memory_kb // 4,
        DB_TYPE_MIXED: (total_memory_kb * 3) // 4
    }[db_type]

    maintenance_work_mem = {
        DB_TYPE_WEB: total_memory_kb // 16,
        DB_TYPE_OLTP: total_memory_kb // 16,
        DB_TYPE_DW: total_memory_kb // 8,
        DB_TYPE_DESKTOP: total_memory_kb // 16,
        DB_TYPE_MIXED: total_memory_kb // 16
    }[db_type]

    memory_limit = (2 * SIZE_UNIT_MAP['GB']) // SIZE_UNIT_MAP['KB']
    if maintenance_work_mem >= memory_limit:
        if os_type == OS_WINDOWS:
            maintenance_work_mem = memory_limit - (1 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
        else:
            maintenance_work_mem = memory_limit

    checkpoint_segments = [
        {
            'key': 'min_wal_size',
            'value': {
                DB_TYPE_WEB: (1024 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_OLTP: (2048 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_DW: (4096 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_DESKTOP: (100 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_MIXED: (1024 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
            }[db_type]
        },
        {
            'key': 'max_wal_size',
            'value': {
                DB_TYPE_WEB: (4096 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_OLTP: (8192 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_DW: (16384 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_DESKTOP: (2048 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB'],
                DB_TYPE_MIXED: (4096 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
            }[db_type]
        }
    ]

    min_wal_size = checkpoint_segments[0]['value']
    max_wal_size = checkpoint_segments[1]['value']

    checkpoint_completion_target = 0.9

    wal_buffers = (3 * shared_buffers) // 100
    max_wal_buffer = (16 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
    if wal_buffers > max_wal_buffer:
        wal_buffers = max_wal_buffer

    wal_buffer_near_value = (14 * SIZE_UNIT_MAP['MB']) // SIZE_UNIT_MAP['KB']
    if wal_buffer_near_value < wal_buffers < max_wal_buffer:
        wal_buffers = max_wal_buffer

    if wal_buffers < 32:
        wal_buffers = 32

    default_statistics_target = {
        DB_TYPE_WEB: 100,
        DB_TYPE_OLTP: 100,
        DB_TYPE_DW: 500,
        DB_TYPE_DESKTOP: 100,
        DB_TYPE_MIXED: 100
    }[db_type]

    random_page_cost = {
        HARD_DRIVE_SSD: 1.1,
        HARD_DRIVE_SAN: 1.1,
        HARD_DRIVE_HDD: 4
    }[hd_type]

    effective_io_concurrency = None
    if os_type not in [OS_WINDOWS, OS_MAC]:
        effective_io_concurrency = {
            HARD_DRIVE_HDD: 2,
            HARD_DRIVE_SSD: 200,
            HARD_DRIVE_SAN: 300
        }[hd_type]

    parallel_settings = []
    if cpu_num >= 4:
        workers_per_gather = ceil(cpu_num / 2)
        if db_type != DB_TYPE_DW and workers_per_gather > 4:
            workers_per_gather = 4

        parallel_settings = [
            {
                'key': 'max_worker_processes',
                'value': cpu_num
            },
            {
                'key': 'max_parallel_workers_per_gather',
                'value': workers_per_gather
            }
        ]

        if db_version >= 10:
            parallel_settings.append({
                'key': 'max_parallel_workers',
                'value': cpu_num
            })

        if db_version >= 11:
            parallel_maintenance_workers = ceil(cpu_num / 2)
            if parallel_maintenance_workers > 4:
                parallel_maintenance_workers = 4

            parallel_settings.append({
                'key': 'max_parallel_maintenance_workers',
                'value': parallel_maintenance_workers
            })

    max_parallel_workers_per_gather = next(
        (param['value'] for param in parallel_settings if param['key'] == 'max_parallel_workers_per_gather'),
        db_default_values.get('max_parallel_workers_per_gather', 1)
    )

    work_mem = (total_memory_kb - shared_buffers) // (max_connections * 3) // max_parallel_workers_per_gather
    work_mem_result = {
        DB_TYPE_WEB: work_mem,
        DB_TYPE_OLTP: work_mem,
        DB_TYPE_DW: work_mem // 2,
        DB_TYPE_DESKTOP: work_mem // 6,
        DB_TYPE_MIXED: work_mem // 2
    }[db_type]

    if work_mem_result < 64:
        work_mem_result = 64

    warning_info_messages = []
    if total_memory_bytes < 256 * SIZE_UNIT_MAP['MB']:
        warning_info_messages = ['WARNING', 'this tool not being optimal', 'for low memory systems']
    elif total_memory_bytes > 100 * SIZE_UNIT_MAP['GB']:
        warning_info_messages = ['WARNING', 'this tool not being optimal', 'for very high memory systems']

    pgtune_out_conf = {
        'max_connections': max_connections,
        'shared_buffers': shared_buffers,
        'effective_cache_size': effective_cache_size,
        'maintenance_work_mem': maintenance_work_mem,
        # 'checkpoint_segments': checkpoint_segments,
        'min_wal_size': min_wal_size,
        'max_wal_size': max_wal_size,
        'checkpoint_completion_target': checkpoint_completion_target,
        'wal_buffers': wal_buffers,
        'default_statistics_target': default_statistics_target,
        'random_page_cost': random_page_cost,
        'effective_io_concurrency': effective_io_concurrency,
        'work_mem': work_mem_result,
        # 'parallel_settings': parallel_settings,
        'max_worker_processes': parallel_settings[0]['value'],
        'max_parallel_workers_per_gather': parallel_settings[1]['value'],
        'max_parallel_workers': parallel_settings[2]['value'],
        'max_parallel_maintenance_workers': parallel_settings[3]['value'],
        # 'warning_info_messages': warning_info_messages,
        'huge_pages': huge_pages
    }

    if log:
        for key, value in pgtune_out_conf.items():
            print(f'{key}: {value}')

    return pgtune_out_conf

conf = pgtune()

