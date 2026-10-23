#include "slang-cuda-prelude.h"

struct Runtime_0
{
    ulonglong nextOrder_0;
};

struct GlobalParams_0
{
    StructuredBuffer<uint> commands_0;
    RWStructuredBuffer<uint> results_0;
    RWStructuredBuffer<Runtime_0> runtimeStates_0;
};

extern "C" __constant__ GlobalParams_0 SLANG_globalParams;
#define globalParams_0 (&SLANG_globalParams)
static __device__ uint daAt_0(uint base_0, uint object_0)
{
    return base_0 + object_0 * 24U;
}

static __device__ uint daFree_0(uint base_1, uint capacity_0)
{
    uint i_0 = 0U;
    for(;;)
    {
        if(i_0 < capacity_0)
        {
        }
        else
        {
            break;
        }
        if((*(&(globalParams_0->results_0)[daAt_0(base_1, i_0) + 22U])) == 0U)
        {
            return i_0;
        }
        i_0 = i_0 + 1U;
    }
    return 4294967295U;
}

static __device__ uint nextProbeOrder_0(uint id_0)
{
    ulonglong next_0 = (&(globalParams_0->runtimeStates_0)[id_0])->nextOrder_0 + 1ULL;
    (&(globalParams_0->runtimeStates_0)[id_0])->nextOrder_0 = next_0;
    return uint(next_0);
}

static __device__ ulonglong probeNumber_0(uint at_0)
{
    uint _S1 = __ldg((&(globalParams_0->commands_0)[at_0]));
    ulonglong _S2 = ulonglong(_S1);
    uint _S3 = __ldg((&(globalParams_0->commands_0)[at_0 + 1U]));
    return _S2 | (ulonglong(_S3) << int(32));
}

static __device__ bool f64Finite_0(ulonglong x_0)
{
    return (x_0 & 9223372036854775807ULL) < 9218868437227405312ULL;
}

static __device__ void daUnlink_0(uint base_2, uint header_0, uint object_1)
{
    uint at_1 = daAt_0(base_2, object_1);
    if(((*(&(globalParams_0->results_0)[at_1 + 22U])) & 512U) == 0U)
    {
        return;
    }
    uint _S4 = at_1 + 7U;
    uint next_1 = *(&(globalParams_0->results_0)[_S4]);
    uint _S5 = at_1 + 8U;
    uint * _S6 = (&(globalParams_0->results_0)[_S5]);
    uint previous_0 = *_S6;
    if((*_S6) == 0U)
    {
        *(&(globalParams_0->results_0)[header_0]) = next_1;
    }
    else
    {
        *(&(globalParams_0->results_0)[daAt_0(base_2, previous_0 - 1U) + 7U]) = next_1;
    }
    if(next_1 == 0U)
    {
        *(&(globalParams_0->results_0)[header_0 + 1U]) = previous_0;
    }
    else
    {
        *(&(globalParams_0->results_0)[daAt_0(base_2, next_1 - 1U) + 8U]) = previous_0;
    }
    *(&(globalParams_0->results_0)[_S4]) = 0U;
    *(&(globalParams_0->results_0)[_S5]) = 0U;
    return;
}

static __device__ void daStore_0(uint at_2, ulonglong value_0)
{
    *(&(globalParams_0->results_0)[at_2]) = uint(value_0);
    *(&(globalParams_0->results_0)[at_2 + 1U]) = uint(value_0 >> int(32));
    return;
}

static __device__ void daLink_0(uint base_3, uint header_1, uint capacity_1, uint object_2)
{
    uint at_3 = daAt_0(base_3, object_2);
    uint _S7 = *(&(globalParams_0->results_0)[at_3 + 20U]);
    uint next_2 = *(&(globalParams_0->results_0)[header_1]);
    uint previous_1 = 0U;
    uint pass_0 = 0U;
    for(;;)
    {
        bool _S8;
        if(pass_0 < capacity_1)
        {
            _S8 = next_2 != 0U;
        }
        else
        {
            _S8 = false;
        }
        if(_S8)
        {
        }
        else
        {
            break;
        }
        uint _S9 = daAt_0(base_3, next_2 - 1U);
        if((*(&(globalParams_0->results_0)[_S9 + 20U])) > _S7)
        {
            break;
        }
        uint _S10 = *(&(globalParams_0->results_0)[_S9 + 7U]);
        uint _S11 = pass_0 + 1U;
        previous_1 = next_2;
        next_2 = _S10;
        pass_0 = _S11;
    }
    *(&(globalParams_0->results_0)[at_3 + 7U]) = next_2;
    *(&(globalParams_0->results_0)[at_3 + 8U]) = previous_1;
    if(previous_1 == 0U)
    {
        *(&(globalParams_0->results_0)[header_1]) = object_2 + 1U;
    }
    else
    {
        *(&(globalParams_0->results_0)[daAt_0(base_3, previous_1 - 1U) + 7U]) = object_2 + 1U;
    }
    if(next_2 == 0U)
    {
        *(&(globalParams_0->results_0)[header_1 + 1U]) = object_2 + 1U;
    }
    else
    {
        *(&(globalParams_0->results_0)[daAt_0(base_3, next_2 - 1U) + 8U]) = object_2 + 1U;
    }
    return;
}

static __device__ uint daArchive_0(uint base_4, uint capacity_2, uint name_0, bool create_0, uint * status_0)
{
    *status_0 = 0U;
    uint i_1 = 0U;
    for(;;)
    {
        if(i_1 < capacity_2)
        {
        }
        else
        {
            break;
        }
        uint at_4 = daAt_0(base_4, i_1);
        bool _S12;
        if(((*(&(globalParams_0->results_0)[at_4 + 22U])) & 255U) == 14U)
        {
            _S12 = (*(&(globalParams_0->results_0)[at_4 + 4U])) == name_0;
        }
        else
        {
            _S12 = false;
        }
        if(_S12)
        {
            return i_1;
        }
        i_1 = i_1 + 1U;
    }
    if(!create_0)
    {
        return 4294967295U;
    }
    uint object_3 = daFree_0(base_4, capacity_2);
    if(object_3 == 4294967295U)
    {
        *status_0 = 64U;
        return object_3;
    }
    uint at_5 = daAt_0(base_4, object_3);
    uint w_0 = 0U;
    for(;;)
    {
        if(w_0 < 24U)
        {
        }
        else
        {
            break;
        }
        *(&(globalParams_0->results_0)[at_5 + w_0]) = 0U;
        w_0 = w_0 + 1U;
    }
    *(&(globalParams_0->results_0)[at_5 + 4U]) = name_0;
    *(&(globalParams_0->results_0)[at_5 + 22U]) = 65550U;
    return object_3;
}

static __device__ void daRemember_0(uint base_5, uint capacity_3, uint name_1, ulonglong value_1, uint * status_1)
{
    uint object_4 = daArchive_0(base_5, capacity_3, name_1, true, status_1);
    if((*status_1) == 0U)
    {
        daStore_0(daAt_0(base_5, object_4), value_1);
    }
    return;
}

static __device__ void daInitializePool_0(uint base_6, uint capacity_4, uint header_2, uint object_5, uint name_2, uint owner_0, uint stat_0, uint order_0, uint slot_0, ulonglong cap_0, uint * status_2)
{
    *status_2 = 0U;
    bool _S13;
    if(object_5 >= capacity_4)
    {
        _S13 = true;
    }
    else
    {
        _S13 = owner_0 >= 5U;
    }
    if(_S13)
    {
        _S13 = true;
    }
    else
    {
        if(stat_0 != 81U)
        {
            _S13 = stat_0 != 82U;
        }
        else
        {
            _S13 = false;
        }
    }
    if(_S13)
    {
        _S13 = true;
    }
    else
    {
        _S13 = order_0 == 0U;
    }
    if(_S13)
    {
        _S13 = true;
    }
    else
    {
        _S13 = !f64Finite_0(cap_0);
    }
    if(_S13)
    {
        *status_2 = 64U;
        return;
    }
    uint at_6 = daAt_0(base_6, object_5);
    daUnlink_0(base_6, header_2, object_5);
    uint w_1 = 0U;
    for(;;)
    {
        if(w_1 < 24U)
        {
        }
        else
        {
            break;
        }
        *(&(globalParams_0->results_0)[at_6 + w_1]) = 0U;
        w_1 = w_1 + 1U;
    }
    daStore_0(at_6 + 2U, cap_0);
    *(&(globalParams_0->results_0)[at_6 + 4U]) = name_2;
    *(&(globalParams_0->results_0)[at_6 + 20U]) = order_0;
    *(&(globalParams_0->results_0)[at_6 + 21U]) = slot_0;
    uint * _S14 = (&(globalParams_0->results_0)[at_6 + 22U]);
    if(stat_0 == 81U)
    {
        w_1 = 13U;
    }
    else
    {
        w_1 = 16U;
    }
    *_S14 = ((w_1 | 512U) | 65536U) | (owner_0 << int(10));
    daLink_0(base_6, header_2, capacity_4, object_5);
    if(name_2 != 4294967295U)
    {
        daRemember_0(base_6, capacity_4, name_2, 0ULL, status_2);
    }
    return;
}

static __device__ void daUpdateOwnerHP_0(uint base_7, uint capacity_5, uint owner_1, ulonglong hp_0, uint * status_3)
{
    *status_3 = 0U;
    bool _S15;
    if(owner_1 >= 5U)
    {
        _S15 = true;
    }
    else
    {
        _S15 = !f64Finite_0(hp_0);
    }
    if(_S15)
    {
        *status_3 = 64U;
        return;
    }
    uint i_2 = 0U;
    for(;;)
    {
        if(i_2 < capacity_5)
        {
        }
        else
        {
            break;
        }
        uint at_7 = daAt_0(base_7, i_2);
        uint * _S16 = (&(globalParams_0->results_0)[at_7 + 22U]);
        uint flags_0 = *_S16;
        if(((*_S16) & 255U) == 15U)
        {
            _S15 = ((flags_0 >> int(10)) & 7U) == owner_1;
        }
        else
        {
            _S15 = false;
        }
        if(_S15)
        {
            daStore_0(at_7 + 2U, hp_0);
        }
        i_2 = i_2 + 1U;
    }
    return;
}

static __device__ void daInitializeRate_0(uint base_8, uint capacity_6, uint header_3, uint object_6, uint name_3, uint owner_2, uint order_1, uint policy_0, ulonglong value_2, uint stack_0, ulonglong hp_1, uint * status_4)
{
    *status_4 = 0U;
    bool _S17;
    if(object_6 >= capacity_6)
    {
        _S17 = true;
    }
    else
    {
        _S17 = owner_2 >= 5U;
    }
    if(_S17)
    {
        _S17 = true;
    }
    else
    {
        _S17 = order_1 == 0U;
    }
    if(_S17)
    {
        _S17 = true;
    }
    else
    {
        _S17 = policy_0 > 15U;
    }
    if(_S17)
    {
        *status_4 = 64U;
        return;
    }
    if(!f64Finite_0(value_2))
    {
        _S17 = true;
    }
    else
    {
        _S17 = !f64Finite_0(hp_1);
    }
    if(_S17)
    {
        *status_4 = 16U;
        return;
    }
    uint at_8 = daAt_0(base_8, object_6);
    daUnlink_0(base_8, header_3, object_6);
    uint w_2 = 0U;
    for(;;)
    {
        if(w_2 < 24U)
        {
        }
        else
        {
            break;
        }
        *(&(globalParams_0->results_0)[at_8 + w_2]) = 0U;
        w_2 = w_2 + 1U;
    }
    daStore_0(at_8, value_2);
    *(&(globalParams_0->results_0)[at_8 + 4U]) = name_3;
    *(&(globalParams_0->results_0)[at_8 + 5U]) = policy_0;
    *(&(globalParams_0->results_0)[at_8 + 20U]) = order_1;
    *(&(globalParams_0->results_0)[at_8 + 21U]) = stack_0;
    *(&(globalParams_0->results_0)[at_8 + 22U]) = 66063U | (owner_2 << int(10));
    daLink_0(base_8, header_3, capacity_6, object_6);
    daUpdateOwnerHP_0(base_8, capacity_6, owner_2, hp_1, status_4);
    return;
}

static __device__ bool f64Nan_0(ulonglong x_1)
{
    return (x_1 & 9223372036854775807ULL) > 9218868437227405312ULL;
}

static __device__ bool f64Zero_0(ulonglong x_2)
{
    return (x_2 & 9223372036854775807ULL) == 0ULL;
}

static __device__ bool f64Equal_0(ulonglong a_0, ulonglong b_0)
{
    bool _S18;
    if(!f64Nan_0(a_0))
    {
        _S18 = !f64Nan_0(b_0);
    }
    else
    {
        _S18 = false;
    }
    if(_S18)
    {
        if(a_0 == b_0)
        {
            _S18 = true;
        }
        else
        {
            if(f64Zero_0(a_0))
            {
                _S18 = f64Zero_0(b_0);
            }
            else
            {
                _S18 = false;
            }
        }
    }
    else
    {
        _S18 = false;
    }
    return _S18;
}

static __device__ bool f64Less_0(ulonglong a_1, ulonglong b_1)
{
    bool _S19;
    if(f64Nan_0(a_1))
    {
        _S19 = true;
    }
    else
    {
        _S19 = f64Nan_0(b_1);
    }
    if(_S19)
    {
        _S19 = true;
    }
    else
    {
        _S19 = f64Equal_0(a_1, b_1);
    }
    if(_S19)
    {
        return false;
    }
    bool negativeA_0 = (a_1 & 9223372036854775808ULL) != 0ULL;
    if(negativeA_0 != ((b_1 & 9223372036854775808ULL) != 0ULL))
    {
        return negativeA_0;
    }
    if(negativeA_0)
    {
        _S19 = a_1 > b_1;
    }
    else
    {
        _S19 = a_1 < b_1;
    }
    return _S19;
}

static __device__ ulonglong daNumber_0(uint at_9)
{
    return ulonglong(*(&(globalParams_0->results_0)[at_9])) | (ulonglong(*(&(globalParams_0->results_0)[at_9 + 1U])) << int(32));
}

static __device__ ulonglong shiftJam_0(ulonglong x_3, uint distance_0)
{
    if(distance_0 == 0U)
    {
        return x_3;
    }
    int _S20;
    if(distance_0 >= 64U)
    {
        if(x_3 != 0ULL)
        {
            _S20 = int(1);
        }
        else
        {
            _S20 = int(0);
        }
        return ulonglong(_S20);
    }
    ulonglong _S21 = x_3 >> distance_0;
    if((x_3 << (64U - distance_0)) != 0ULL)
    {
        _S20 = int(1);
    }
    else
    {
        _S20 = int(0);
    }
    return _S21 | ulonglong(_S20);
}

static __device__ ulonglong f64Pack_0(ulonglong sign_0, int exponent_0, ulonglong significand_0)
{
    bool _S22;
    if(significand_0 == 0ULL)
    {
        return sign_0;
    }
    ulonglong rounded_0;
    int _S23;
    if(significand_0 >= 72057594037927936ULL)
    {
        int _S24 = exponent_0 + int(1);
        rounded_0 = shiftJam_0(significand_0, 1U);
        _S23 = _S24;
    }
    else
    {
        rounded_0 = significand_0;
        _S23 = exponent_0;
    }
    for(;;)
    {
        if(rounded_0 < 36028797018963968ULL)
        {
            _S22 = _S23 > int(1);
        }
        else
        {
            _S22 = false;
        }
        if(_S22)
        {
        }
        else
        {
            break;
        }
        int _S25 = _S23 - int(1);
        rounded_0 = rounded_0 << int(1);
        _S23 = _S25;
    }
    if(_S23 < int(1))
    {
        rounded_0 = shiftJam_0(rounded_0, uint(int(1) - _S23));
        _S23 = int(1);
    }
    uint tail_0 = uint(rounded_0 & 7ULL);
    ulonglong rounded_1 = rounded_0 >> int(3);
    if(tail_0 > 4U)
    {
        _S22 = true;
    }
    else
    {
        if(tail_0 == 4U)
        {
            _S22 = (rounded_1 & 1ULL) != 0ULL;
        }
        else
        {
            _S22 = false;
        }
    }
    if(_S22)
    {
        rounded_0 = rounded_1 + 1ULL;
    }
    else
    {
        rounded_0 = rounded_1;
    }
    if(rounded_0 >= 9007199254740992ULL)
    {
        ulonglong rounded_2 = rounded_0 >> int(1);
        _S23 = _S23 + int(1);
        rounded_0 = rounded_2;
    }
    if(_S23 >= int(2047))
    {
        return sign_0 | 9218868437227405312ULL;
    }
    if(rounded_0 < 4503599627370496ULL)
    {
        _S23 = int(0);
    }
    return (sign_0 | (ulonglong(_S23) << int(52))) | (rounded_0 & 4503599627370495ULL);
}

static __device__ ulonglong f64FromI64_0(ulonglong integer_0)
{
    ulonglong sign_1 = integer_0 & 9223372036854775808ULL;
    ulonglong magnitude_0;
    if(sign_1 != 0ULL)
    {
        magnitude_0 = ~integer_0 + 1ULL;
    }
    else
    {
        magnitude_0 = integer_0;
    }
    if(magnitude_0 == 0ULL)
    {
        return 0ULL;
    }
    ulonglong scan_0 = magnitude_0;
    uint highest_0 = 0U;
    for(;;)
    {
        if(scan_0 > 1ULL)
        {
        }
        else
        {
            break;
        }
        uint _S26 = highest_0 + 1U;
        scan_0 = scan_0 >> int(1);
        highest_0 = _S26;
    }
    ulonglong extended_0;
    if(highest_0 > 55U)
    {
        extended_0 = shiftJam_0(magnitude_0, highest_0 - 55U);
    }
    else
    {
        extended_0 = magnitude_0 << (55U - highest_0);
    }
    return f64Pack_0(sign_1, int(highest_0) + int(1023), extended_0);
}

static __device__ __noinline__ ulonglong f64Add_0(ulonglong a_2, ulonglong b_2)
{
    bool _S27;
    if(f64Nan_0(a_2))
    {
        _S27 = true;
    }
    else
    {
        _S27 = f64Nan_0(b_2);
    }
    if(_S27)
    {
        return 9221120237041090560ULL;
    }
    ulonglong ma_0 = a_2 & 9223372036854775807ULL;
    ulonglong mb_0 = b_2 & 9223372036854775807ULL;
    bool _S28 = ma_0 == 9218868437227405312ULL;
    if(_S28)
    {
        _S27 = true;
    }
    else
    {
        _S27 = mb_0 == 9218868437227405312ULL;
    }
    ulonglong _S29;
    if(_S27)
    {
        if(ma_0 == mb_0)
        {
            _S27 = ((a_2 ^ b_2) & 9223372036854775808ULL) != 0ULL;
        }
        else
        {
            _S27 = false;
        }
        if(_S27)
        {
            return 9221120237041090560ULL;
        }
        if(_S28)
        {
            _S29 = a_2;
        }
        else
        {
            _S29 = b_2;
        }
        return _S29;
    }
    ulonglong _S30;
    if(ma_0 < mb_0)
    {
        _S29 = b_2;
        _S30 = a_2;
    }
    else
    {
        _S29 = a_2;
        _S30 = b_2;
    }
    ulonglong _S31 = _S29 & 4503599627370495ULL;
    ulonglong _S32 = (_S29 >> int(52)) & 2047ULL;
    ulonglong _S33;
    if(_S32 != 0ULL)
    {
        _S33 = 4503599627370496ULL;
    }
    else
    {
        _S33 = 0ULL;
    }
    ulonglong sa_0 = _S31 | _S33;
    ulonglong _S34 = _S30 & 4503599627370495ULL;
    ulonglong _S35 = (_S30 >> int(52)) & 2047ULL;
    if(_S35 != 0ULL)
    {
        _S33 = 4503599627370496ULL;
    }
    else
    {
        _S33 = 0ULL;
    }
    int _S36 = (I32_max((int(1)), (int(_S32))));
    ulonglong sa_1 = sa_0 << int(3);
    ulonglong sb_0 = shiftJam_0((_S34 | _S33) << int(3), uint(_S36 - (I32_max((int(1)), (int(_S35))))));
    if(((_S29 ^ _S30) & 9223372036854775808ULL) == 0ULL)
    {
        return f64Pack_0(_S29 & 9223372036854775808ULL, _S36, sa_1 + sb_0);
    }
    if(sa_1 == sb_0)
    {
        return 0ULL;
    }
    return f64Pack_0(_S29 & 9223372036854775808ULL, _S36, sa_1 - sb_0);
}

static __device__ void f64Unpack_0(ulonglong bits_0, int * exponent_1, ulonglong * significand_1)
{
    *exponent_1 = int((bits_0 >> int(52)) & 2047ULL);
    *significand_1 = bits_0 & 4503599627370495ULL;
    if((*exponent_1) != int(0))
    {
        *significand_1 = (*significand_1) | 4503599627370496ULL;
    }
    else
    {
        *exponent_1 = int(1);
        for(;;)
        {
            if((*significand_1) < 4503599627370496ULL)
            {
            }
            else
            {
                break;
            }
            *significand_1 = (*significand_1) << int(1);
            *exponent_1 = *exponent_1 - int(1);
        }
    }
    return;
}

static __device__ void mulWide_0(ulonglong a_3, ulonglong b_3, ulonglong * hi_0, ulonglong * lo_0)
{
    ulonglong al_0 = ulonglong(uint(a_3));
    ulonglong ah_0 = a_3 >> int(32);
    ulonglong bl_0 = ulonglong(uint(b_3));
    ulonglong bh_0 = b_3 >> int(32);
    ulonglong p_0 = al_0 * bl_0;
    ulonglong middle_0 = ah_0 * bl_0 + (p_0 >> int(32));
    ulonglong middle_1 = ulonglong(uint(middle_0)) + al_0 * bh_0;
    *hi_0 = ah_0 * bh_0 + (middle_0 >> int(32)) + (middle_1 >> int(32));
    *lo_0 = (middle_1 << int(32)) | ulonglong(uint(p_0));
    return;
}

static __device__ __noinline__ ulonglong f64Mul_0(ulonglong a_4, ulonglong b_4)
{
    ulonglong sign_2 = (a_4 ^ b_4) & 9223372036854775808ULL;
    ulonglong ma_1 = a_4 & 9223372036854775807ULL;
    ulonglong mb_1 = b_4 & 9223372036854775807ULL;
    bool _S37;
    if(f64Nan_0(a_4))
    {
        _S37 = true;
    }
    else
    {
        _S37 = f64Nan_0(b_4);
    }
    if(_S37)
    {
        return 9221120237041090560ULL;
    }
    if(ma_1 == 9218868437227405312ULL)
    {
        _S37 = true;
    }
    else
    {
        _S37 = mb_1 == 9218868437227405312ULL;
    }
    if(_S37)
    {
        if(ma_1 == 0ULL)
        {
            _S37 = true;
        }
        else
        {
            _S37 = mb_1 == 0ULL;
        }
        ulonglong _S38;
        if(_S37)
        {
            _S38 = 9221120237041090560ULL;
        }
        else
        {
            _S38 = sign_2 | 9218868437227405312ULL;
        }
        return _S38;
    }
    if(ma_1 == 0ULL)
    {
        _S37 = true;
    }
    else
    {
        _S37 = mb_1 == 0ULL;
    }
    if(_S37)
    {
        return sign_2;
    }
    int ea_0;
    ulonglong sa_2;
    f64Unpack_0(a_4, &ea_0, &sa_2);
    int eb_0;
    ulonglong sb_1;
    f64Unpack_0(b_4, &eb_0, &sb_1);
    ulonglong hi_1;
    ulonglong lo_1;
    mulWide_0(sa_2, sb_1, &hi_1, &lo_1);
    ulonglong sig_0 = (hi_1 << int(15)) | (lo_1 >> int(49));
    int _S39;
    if((lo_1 << int(15)) != 0ULL)
    {
        _S39 = int(1);
    }
    else
    {
        _S39 = int(0);
    }
    return f64Pack_0(sign_2, ea_0 + eb_0 - int(1023), sig_0 | ulonglong(_S39));
}

static __device__ ulonglong daRate_0(uint base_9, uint capacity_7, uint header_4, uint pool_0, uint * status_5)
{
    *status_5 = 0U;
    uint p_1 = daAt_0(base_9, pool_0);
    uint _S40 = ((*(&(globalParams_0->results_0)[p_1 + 22U])) >> int(10)) & 7U;
    uint _S41 = *(&(globalParams_0->results_0)[p_1 + 4U]);
    uint next_3 = *(&(globalParams_0->results_0)[header_4]);
    ulonglong baseline_0 = 0ULL;
    ulonglong add_0 = 0ULL;
    bool present_0 = false;
    uint pass_1 = 0U;
    for(;;)
    {
        bool _S42;
        if(pass_1 < capacity_7)
        {
            _S42 = next_3 != 0U;
        }
        else
        {
            _S42 = false;
        }
        if(_S42)
        {
        }
        else
        {
            break;
        }
        uint at_10 = daAt_0(base_9, next_3 - 1U);
        uint * _S43 = (&(globalParams_0->results_0)[at_10 + 22U]);
        uint flags_1 = *_S43;
        uint _S44 = *(&(globalParams_0->results_0)[at_10 + 7U]);
        bool _S45;
        if(((*_S43) & 255U) != 15U)
        {
            _S45 = true;
        }
        else
        {
            _S45 = ((flags_1 >> int(10)) & 7U) != _S40;
        }
        if(_S45)
        {
            uint _S46 = pass_1 + 1U;
            next_3 = _S44;
            pass_1 = _S46;
            continue;
        }
        uint * _S47 = (&(globalParams_0->results_0)[at_10 + 5U]);
        uint policy_1 = *_S47;
        if(((*_S47) & 1U) == 0U)
        {
            uint _S46 = pass_1 + 1U;
            next_3 = _S44;
            pass_1 = _S46;
            continue;
        }
        ulonglong value_3 = daNumber_0(at_10);
        ulonglong value_4;
        if((policy_1 & 4U) != 0U)
        {
            ulonglong lost_0 = f64Add_0(f64FromI64_0(100ULL), (daNumber_0(at_10 + 2U)) ^ 9223372036854775808ULL);
            if(f64Less_0(lost_0, 0ULL))
            {
                value_4 = 0ULL;
            }
            else
            {
                value_4 = lost_0;
            }
            value_4 = f64Mul_0(value_3, value_4);
        }
        else
        {
            if((policy_1 & 8U) != 0U)
            {
                value_4 = f64Mul_0(value_3, f64FromI64_0(ulonglong(*(&(globalParams_0->results_0)[at_10 + 21U]))));
            }
            else
            {
                value_4 = value_3;
            }
        }
        if(!f64Finite_0(value_4))
        {
            *status_5 = 16U;
            return 0ULL;
        }
        ulonglong baseline_1;
        ulonglong add_1;
        bool present_1;
        if((policy_1 & 2U) == 0U)
        {
            if(f64Zero_0(baseline_0))
            {
                baseline_1 = 0ULL;
            }
            else
            {
                baseline_1 = baseline_0;
            }
            baseline_1 = f64Add_0(baseline_1, value_4);
            add_1 = add_0;
            present_1 = true;
        }
        else
        {
            if((*(&(globalParams_0->results_0)[at_10 + 4U])) == _S41)
            {
                baseline_1 = f64Add_0(add_0, value_4);
            }
            else
            {
                baseline_1 = add_0;
            }
            ulonglong _S48 = baseline_1;
            baseline_1 = baseline_0;
            add_1 = _S48;
            present_1 = present_0;
        }
        baseline_0 = baseline_1;
        add_0 = add_1;
        present_0 = present_1;
        uint _S46 = pass_1 + 1U;
        next_3 = _S44;
        pass_1 = _S46;
    }
    if(present_0)
    {
    }
    else
    {
        baseline_0 = f64FromI64_0(100ULL);
    }
    ulonglong rate_0 = f64Add_0(baseline_0, add_0);
    if(!f64Finite_0(rate_0))
    {
        *status_5 = 16U;
    }
    return rate_0;
}

static __device__ __noinline__ ulonglong f64Div_0(ulonglong a_5, ulonglong b_5)
{
    ulonglong sign_3 = (a_5 ^ b_5) & 9223372036854775808ULL;
    ulonglong ma_2 = a_5 & 9223372036854775807ULL;
    ulonglong mb_2 = b_5 & 9223372036854775807ULL;
    bool _S49;
    if(f64Nan_0(a_5))
    {
        _S49 = true;
    }
    else
    {
        _S49 = f64Nan_0(b_5);
    }
    if(_S49)
    {
        _S49 = true;
    }
    else
    {
        if(ma_2 == 9218868437227405312ULL)
        {
            _S49 = mb_2 == 9218868437227405312ULL;
        }
        else
        {
            _S49 = false;
        }
    }
    if(_S49)
    {
        _S49 = true;
    }
    else
    {
        if(ma_2 == 0ULL)
        {
            _S49 = mb_2 == 0ULL;
        }
        else
        {
            _S49 = false;
        }
    }
    if(_S49)
    {
        return 9221120237041090560ULL;
    }
    if(ma_2 == 9218868437227405312ULL)
    {
        _S49 = true;
    }
    else
    {
        _S49 = mb_2 == 0ULL;
    }
    if(_S49)
    {
        return sign_3 | 9218868437227405312ULL;
    }
    if(ma_2 == 0ULL)
    {
        _S49 = true;
    }
    else
    {
        _S49 = mb_2 == 9218868437227405312ULL;
    }
    if(_S49)
    {
        return sign_3;
    }
    int ea_1;
    ulonglong remainder_0;
    f64Unpack_0(a_5, &ea_1, &remainder_0);
    int eb_1;
    ulonglong divisor_0;
    f64Unpack_0(b_5, &eb_1, &divisor_0);
    int exponent_2 = ea_1 - eb_1 + int(1023);
    int exponent_3;
    if(remainder_0 < divisor_0)
    {
        remainder_0 = remainder_0 << int(1);
        exponent_3 = exponent_2 - int(1);
    }
    else
    {
        exponent_3 = exponent_2;
    }
    uint bit_0 = 0U;
    ulonglong sig_1 = 0ULL;
    for(;;)
    {
        if(bit_0 < 56U)
        {
        }
        else
        {
            break;
        }
        ulonglong sig_2 = sig_1 << int(1);
        if(remainder_0 >= divisor_0)
        {
            remainder_0 = remainder_0 - divisor_0;
            sig_1 = sig_2 | 1ULL;
        }
        else
        {
            sig_1 = sig_2;
        }
        if(bit_0 < 55U)
        {
            remainder_0 = remainder_0 << int(1);
        }
        bit_0 = bit_0 + 1U;
    }
    int _S50;
    if(remainder_0 != 0ULL)
    {
        _S50 = int(1);
    }
    else
    {
        _S50 = int(0);
    }
    return f64Pack_0(sign_3, exponent_3, sig_1 | ulonglong(_S50));
}

static __device__ uint daCollect_0(uint base_10, uint capacity_8, uint header_5, uint owner_3, ulonglong damage_0, uint queue_0, uint queueCapacity_0, uint * status_6)
{
    *status_6 = 0U;
    if(!f64Finite_0(damage_0))
    {
        *status_6 = 16U;
        return 0U;
    }
    if(!f64Less_0(0ULL, damage_0))
    {
        return 0U;
    }
    uint group_0 = 0U;
    uint count_0 = 0U;
    for(;;)
    {
        if(group_0 < 2U)
        {
        }
        else
        {
            break;
        }
        uint _S51 = *(&(globalParams_0->results_0)[header_5]);
        uint _S52;
        if(group_0 == 0U)
        {
            _S52 = 13U;
        }
        else
        {
            _S52 = 16U;
        }
        uint next_4 = _S51;
        uint pass_2 = 0U;
        uint count_1 = count_0;
        for(;;)
        {
            bool _S53;
            if(pass_2 < capacity_8)
            {
                _S53 = next_4 != 0U;
            }
            else
            {
                _S53 = false;
            }
            if(_S53)
            {
            }
            else
            {
                break;
            }
            uint chosen_0 = next_4 - 1U;
            uint at_11 = daAt_0(base_10, chosen_0);
            uint _S54 = at_11 + 22U;
            uint * _S55 = (&(globalParams_0->results_0)[_S54]);
            uint flags_2 = *_S55;
            uint _S56 = *(&(globalParams_0->results_0)[at_11 + 7U]);
            uint count_2;
            if(((*_S55) & 255U) != _S52)
            {
                count_2 = count_1;
                uint _S57 = pass_2 + 1U;
                next_4 = _S56;
                pass_2 = _S57;
                count_1 = count_2;
                continue;
            }
            uint caster_0 = (flags_2 >> int(10)) & 7U;
            ulonglong cap_1 = daNumber_0(at_11 + 2U);
            bool _S58;
            if((flags_2 & 262144U) != 0U)
            {
                _S58 = true;
            }
            else
            {
                _S58 = !f64Less_0(0ULL, cap_1);
            }
            bool _S59;
            if(_S58)
            {
                _S59 = true;
            }
            else
            {
                if(_S52 == 13U)
                {
                    _S59 = caster_0 != owner_3;
                }
                else
                {
                    _S59 = false;
                }
            }
            if(_S59)
            {
                count_2 = count_1;
                uint _S57 = pass_2 + 1U;
                next_4 = _S56;
                pass_2 = _S57;
                count_1 = count_2;
                continue;
            }
            ulonglong rate_1 = daRate_0(base_10, capacity_8, header_5, chosen_0, status_6);
            if((*status_6) != 0U)
            {
                return count_1;
            }
            ulonglong current_0 = f64Add_0(daNumber_0(at_11), f64Div_0(f64Mul_0(damage_0, rate_1), f64FromI64_0(100ULL)));
            ulonglong current_1;
            if(f64Less_0(cap_1, current_0))
            {
                current_1 = cap_1;
            }
            else
            {
                current_1 = current_0;
            }
            if(!f64Finite_0(current_1))
            {
                *status_6 = 16U;
                return count_1;
            }
            daStore_0(at_11, current_1);
            uint * _S60 = (&(globalParams_0->results_0)[at_11 + 4U]);
            uint name_4 = *_S60;
            bool _S61 = (*_S60) != 4294967295U;
            if(_S61)
            {
                daRemember_0(base_10, capacity_8, name_4, current_1, status_6);
                if((*status_6) != 0U)
                {
                    return count_1;
                }
            }
            if(!f64Less_0(current_1, f64Add_0(cap_1, 13695778570484766357ULL)))
            {
                uint * _S62 = (&(globalParams_0->results_0)[_S54]);
                *_S62 = (*_S62) | 262144U;
                if(_S61)
                {
                    if(count_1 >= queueCapacity_0)
                    {
                        *status_6 = 64U;
                        return count_1;
                    }
                    uint _S63 = queue_0 + count_1 * 2U;
                    *(&(globalParams_0->results_0)[_S63]) = name_4;
                    *(&(globalParams_0->results_0)[_S63 + 1U]) = caster_0;
                    count_2 = count_1 + 1U;
                }
                else
                {
                    count_2 = count_1;
                }
            }
            else
            {
                count_2 = count_1;
            }
            uint _S57 = pass_2 + 1U;
            next_4 = _S56;
            pass_2 = _S57;
            count_1 = count_2;
        }
        group_0 = group_0 + 1U;
        count_0 = count_1;
    }
    return count_0;
}

static __device__ bool daPool_0(uint flags_3)
{
    uint _S64 = flags_3 & 255U;
    bool _S65;
    if(_S64 == 13U)
    {
        _S65 = true;
    }
    else
    {
        _S65 = _S64 == 16U;
    }
    return _S65;
}

static __device__ ulonglong daTake_0(uint base_11, uint capacity_9, uint header_6, uint name_5, uint * status_7)
{
    uint chosen_1;
    *status_7 = 0U;
    uint next_5 = *(&(globalParams_0->results_0)[header_6]);
    uint pass_3 = 0U;
    for(;;)
    {
        bool _S66;
        if(pass_3 < capacity_9)
        {
            _S66 = next_5 != 0U;
        }
        else
        {
            _S66 = false;
        }
        if(_S66)
        {
        }
        else
        {
            chosen_1 = 4294967295U;
            break;
        }
        uint object_7 = next_5 - 1U;
        uint at_12 = daAt_0(base_11, object_7);
        uint _S67 = *(&(globalParams_0->results_0)[at_12 + 7U]);
        bool _S68;
        if(daPool_0(*(&(globalParams_0->results_0)[at_12 + 22U])))
        {
            _S68 = (*(&(globalParams_0->results_0)[at_12 + 4U])) == name_5;
        }
        else
        {
            _S68 = false;
        }
        if(_S68)
        {
            chosen_1 = object_7;
            break;
        }
        uint _S69 = pass_3 + 1U;
        next_5 = _S67;
        pass_3 = _S69;
    }
    ulonglong value_5;
    if(chosen_1 != 4294967295U)
    {
        uint at_13 = daAt_0(base_11, chosen_1);
        ulonglong _S70 = daNumber_0(at_13);
        daStore_0(at_13, 0ULL);
        uint * _S71 = (&(globalParams_0->results_0)[at_13 + 22U]);
        *_S71 = (*_S71) | 262144U;
        value_5 = _S70;
    }
    else
    {
        uint object_8 = daArchive_0(base_11, capacity_9, name_5, false, status_7);
        if(object_8 != 4294967295U)
        {
            value_5 = daNumber_0(daAt_0(base_11, object_8));
        }
        else
        {
            value_5 = 0ULL;
        }
    }
    daRemember_0(base_11, capacity_9, name_5, 0ULL, status_7);
    return value_5;
}

static __device__ ulonglong f64Abs_0(ulonglong x_4)
{
    return x_4 & 9223372036854775807ULL;
}

static __device__ ulonglong f64Integral_0(ulonglong x_5, uint mode_0)
{
    ulonglong magnitude_1 = f64Abs_0(x_5);
    ulonglong sign_4 = x_5 & 9223372036854775808ULL;
    if(f64Nan_0(x_5))
    {
        return 9221120237041090560ULL;
    }
    int exponent_4 = int((x_5 >> int(52)) & 2047ULL) - int(1023);
    bool one_0;
    if(exponent_4 >= int(52))
    {
        one_0 = true;
    }
    else
    {
        one_0 = magnitude_1 == 0ULL;
    }
    if(one_0)
    {
        return x_5;
    }
    ulonglong rounded_3;
    if(exponent_4 < int(0))
    {
        if(mode_0 == 2U)
        {
            one_0 = sign_4 != 0ULL;
        }
        else
        {
            if(mode_0 == 0U)
            {
                one_0 = magnitude_1 > 4602678819172646912ULL;
            }
            else
            {
                one_0 = false;
            }
        }
        if(one_0)
        {
            rounded_3 = 4607182418800017408ULL;
        }
        else
        {
            rounded_3 = 0ULL;
        }
        return sign_4 | rounded_3;
    }
    ulonglong unit_0 = 1ULL << uint(int(52) - exponent_4);
    ulonglong mask_0 = unit_0 - 1ULL;
    ulonglong tail_1 = magnitude_1 & mask_0;
    ulonglong rounded_4 = magnitude_1 & (~mask_0);
    if(mode_0 == 2U)
    {
        if(sign_4 != 0ULL)
        {
            one_0 = tail_1 != 0ULL;
        }
        else
        {
            one_0 = false;
        }
    }
    else
    {
        if(mode_0 == 0U)
        {
            ulonglong _S72 = unit_0 >> int(1);
            if(tail_1 > _S72)
            {
                one_0 = true;
            }
            else
            {
                if(tail_1 == _S72)
                {
                    one_0 = (rounded_4 & unit_0) != 0ULL;
                }
                else
                {
                    one_0 = false;
                }
            }
        }
        else
        {
            one_0 = false;
        }
    }
    if(one_0)
    {
        rounded_3 = rounded_4 + unit_0;
    }
    else
    {
        rounded_3 = rounded_4;
    }
    return sign_4 | rounded_3;
}

static __device__ ulonglong f64ToI64_0(ulonglong x_6, uint mode_1, uint * status_8)
{
    *status_8 = 0U;
    if(!f64Finite_0(x_6))
    {
        *status_8 = 1U;
        return 0ULL;
    }
    ulonglong rounded_5 = f64Integral_0(x_6, mode_1);
    if((f64Abs_0(rounded_5)) == 0ULL)
    {
        return 0ULL;
    }
    int exponent_5 = int((rounded_5 >> int(52)) & 2047ULL) - int(1023);
    bool negative_0 = (rounded_5 & 9223372036854775808ULL) != 0ULL;
    bool _S73;
    if(exponent_5 > int(63))
    {
        _S73 = true;
    }
    else
    {
        if(exponent_5 == int(63))
        {
            if(!negative_0)
            {
                _S73 = true;
            }
            else
            {
                _S73 = (rounded_5 & 4503599627370495ULL) != 0ULL;
            }
        }
        else
        {
            _S73 = false;
        }
    }
    if(_S73)
    {
        *status_8 = 1U;
        return 0ULL;
    }
    if(exponent_5 < int(0))
    {
        return 0ULL;
    }
    ulonglong significand_2 = (rounded_5 & 4503599627370495ULL) | 4503599627370496ULL;
    ulonglong integer_1;
    if(exponent_5 >= int(52))
    {
        integer_1 = significand_2 << uint(exponent_5 - int(52));
    }
    else
    {
        integer_1 = significand_2 >> uint(int(52) - exponent_5);
    }
    if(negative_0)
    {
        integer_1 = ~integer_1 + 1ULL;
    }
    return integer_1;
}

static __device__ ulonglong daEmission_0(ulonglong amount_0, ulonglong split_0, bool * emit_0, uint * status_9)
{
    *emit_0 = false;
    *status_9 = 0U;
    bool _S74;
    if(!f64Finite_0(amount_0))
    {
        _S74 = true;
    }
    else
    {
        _S74 = !f64Finite_0(split_0);
    }
    if(_S74)
    {
        *status_9 = 16U;
        return 0ULL;
    }
    if(!f64Less_0(0ULL, amount_0))
    {
        return 0ULL;
    }
    *emit_0 = true;
    uint conversion_0;
    ulonglong integer_2 = f64ToI64_0(f64Mul_0(amount_0, f64Add_0(f64FromI64_0(1ULL), f64Div_0(split_0, f64FromI64_0(100ULL)))), 1U, &conversion_0);
    if(conversion_0 != 0U)
    {
        *status_9 = 16U;
        return 0ULL;
    }
    return integer_2;
}

static __device__ void daRetire_0(uint base_12, uint header_7, uint object_9)
{
    daUnlink_0(base_12, header_7, object_9);
    *(&(globalParams_0->results_0)[daAt_0(base_12, object_9) + 22U]) = 0U;
    return;
}

extern "C" __global__ void portableEvents()
{
    bool _S75;
    uint object_10;
    uint _S76 = (blockIdx * blockDim + threadIdx).x;
    uint _S77 = __ldg((&(globalParams_0->commands_0)[int(0)]));
    if(_S76 >= _S77)
    {
        return;
    }
    uint input_0 = 1U + _S76 * 512U;
    uint output_0 = _S76 * 786432U;
    uint _S78 = output_0 + 16U;
    uint header_8 = output_0 + 8U;
    uint status_10 = 0U;
    (&(globalParams_0->runtimeStates_0)[_S76])->nextOrder_0 = 0ULL;
    uint _S79 = __ldg((&(globalParams_0->commands_0)[input_0]));
    uint _S80 = __ldg((&(globalParams_0->commands_0)[input_0 + 1U]));
    bool _S81;
    if(_S79 == 0U)
    {
        _S81 = true;
    }
    else
    {
        _S81 = _S79 > 32U;
    }
    if(_S81)
    {
        _S81 = true;
    }
    else
    {
        _S81 = _S80 > 24U;
    }
    if(_S81)
    {
        *(&(globalParams_0->results_0)[output_0]) = 64U;
        return;
    }
    *(&(globalParams_0->results_0)[header_8]) = 0U;
    *(&(globalParams_0->results_0)[header_8 + 1U]) = 0U;
    uint i_3 = 0U;
    for(;;)
    {
        if(i_3 < 768U)
        {
        }
        else
        {
            break;
        }
        *(&(globalParams_0->results_0)[_S78 + i_3]) = 0U;
        i_3 = i_3 + 1U;
    }
    uint step_0 = 0U;
    for(;;)
    {
        if(step_0 < _S80)
        {
            _S81 = status_10 == 0U;
        }
        else
        {
            _S81 = false;
        }
        if(_S81)
        {
        }
        else
        {
            break;
        }
        uint at_14 = input_0 + 2U + step_0 * 20U;
        uint _S82 = __ldg((&(globalParams_0->commands_0)[at_14]));
        uint _S83 = __ldg((&(globalParams_0->commands_0)[at_14 + 1U]));
        uint answer_0 = output_0 + 1024U + step_0 * 32U;
        *(&(globalParams_0->results_0)[answer_0]) = _S82;
        i_3 = 0U;
        for(;;)
        {
            if(i_3 < _S79)
            {
            }
            else
            {
                object_10 = 4294967295U;
                break;
            }
            uint p_2 = daAt_0(_S78, i_3);
            if(((*(&(globalParams_0->results_0)[p_2 + 22U])) & 512U) != 0U)
            {
                _S75 = (*(&(globalParams_0->results_0)[p_2 + 6U])) == _S83;
            }
            else
            {
                _S75 = false;
            }
            if(_S75)
            {
                object_10 = i_3;
                break;
            }
            i_3 = i_3 + 1U;
        }
        bool _S84 = _S82 == 0U;
        if(_S84)
        {
            _S75 = true;
        }
        else
        {
            _S75 = _S82 == 1U;
        }
        uint object_11;
        if(_S75)
        {
            if(object_10 == 4294967295U)
            {
                object_11 = daFree_0(_S78, _S79);
            }
            else
            {
                object_11 = object_10;
            }
            if(object_11 == 4294967295U)
            {
                status_10 = 64U;
                break;
            }
            uint p_3 = daAt_0(_S78, object_11);
            if(_S84)
            {
                uint _S85 = __ldg((&(globalParams_0->commands_0)[at_14 + 3U]));
                uint _S86 = __ldg((&(globalParams_0->commands_0)[at_14 + 4U]));
                uint _S87 = __ldg((&(globalParams_0->commands_0)[at_14 + 2U]));
                uint _S88 = nextProbeOrder_0(_S76);
                daInitializePool_0(_S78, _S79, header_8, object_11, _S85, _S86, _S87, _S88, _S83, probeNumber_0(at_14 + 5U), &status_10);
            }
            else
            {
                uint _S89 = __ldg((&(globalParams_0->commands_0)[at_14 + 3U]));
                uint _S90 = __ldg((&(globalParams_0->commands_0)[at_14 + 4U]));
                uint _S91 = nextProbeOrder_0(_S76);
                uint _S92 = __ldg((&(globalParams_0->commands_0)[at_14 + 2U]));
                ulonglong _S93 = probeNumber_0(at_14 + 5U);
                uint _S94 = __ldg((&(globalParams_0->commands_0)[at_14 + 7U]));
                daInitializeRate_0(_S78, _S79, header_8, object_11, _S89, _S90, _S91, _S92, _S93, _S94, probeNumber_0(at_14 + 9U), &status_10);
            }
            *(&(globalParams_0->results_0)[p_3 + 6U]) = _S83;
        }
        else
        {
            if(_S82 == 2U)
            {
                uint queue_1 = output_0 + 3072U;
                uint full_0 = daCollect_0(_S78, _S79, header_8, _S83, probeNumber_0(at_14 + 5U), queue_1, 8U, &status_10);
                *(&(globalParams_0->results_0)[answer_0 + 5U]) = full_0;
                object_11 = 0U;
                for(;;)
                {
                    if(object_11 < full_0)
                    {
                    }
                    else
                    {
                        break;
                    }
                    uint _S95 = object_11 * 2U;
                    uint _S96 = queue_1 + _S95;
                    *(&(globalParams_0->results_0)[answer_0 + 6U + _S95]) = *(&(globalParams_0->results_0)[_S96]);
                    *(&(globalParams_0->results_0)[answer_0 + 7U + _S95]) = *(&(globalParams_0->results_0)[_S96 + 1U]);
                    object_11 = object_11 + 1U;
                }
                uint i_4 = 0U;
                uint done_0 = 0U;
                for(;;)
                {
                    if(i_4 < _S79)
                    {
                    }
                    else
                    {
                        break;
                    }
                    uint p_4 = daAt_0(_S78, i_4);
                    uint _S97 = p_4 + 22U;
                    bool _S98;
                    if(daPool_0(*(&(globalParams_0->results_0)[_S97])))
                    {
                        _S98 = ((*(&(globalParams_0->results_0)[_S97])) & 262144U) != 0U;
                    }
                    else
                    {
                        _S98 = false;
                    }
                    if(_S98)
                    {
                        done_0 = done_0 | (1U << (*(&(globalParams_0->results_0)[p_4 + 6U])));
                    }
                    i_4 = i_4 + 1U;
                }
                *(&(globalParams_0->results_0)[answer_0 + 22U]) = done_0;
            }
            else
            {
                if(_S82 == 3U)
                {
                    uint _S99 = __ldg((&(globalParams_0->commands_0)[at_14 + 3U]));
                    ulonglong amount_1 = daTake_0(_S78, _S79, header_8, _S99, &status_10);
                    daStore_0(answer_0 + 2U, amount_1);
                    bool emit_1;
                    uint convert_0;
                    ulonglong integer_3 = daEmission_0(amount_1, probeNumber_0(at_14 + 5U), &emit_1, &convert_0);
                    if(status_10 == 0U)
                    {
                        status_10 = convert_0;
                    }
                    *(&(globalParams_0->results_0)[answer_0 + 4U]) = uint(emit_1);
                    daStore_0(answer_0 + 24U, integer_3);
                }
                else
                {
                    if(_S82 == 4U)
                    {
                        if(object_10 == 4294967295U)
                        {
                            status_10 = 64U;
                        }
                        else
                        {
                            daRetire_0(_S78, header_8, object_10);
                        }
                    }
                    else
                    {
                        if(_S82 == 5U)
                        {
                            if(object_10 == 4294967295U)
                            {
                                status_10 = 64U;
                            }
                            else
                            {
                                ulonglong rate_2 = daRate_0(_S78, _S79, header_8, object_10, &status_10);
                                daStore_0(answer_0 + 2U, rate_2);
                            }
                        }
                        else
                        {
                            if(_S82 == 6U)
                            {
                                daUpdateOwnerHP_0(_S78, _S79, _S83, probeNumber_0(at_14 + 5U), &status_10);
                            }
                            else
                            {
                                status_10 = 64U;
                            }
                        }
                    }
                }
            }
        }
        *(&(globalParams_0->results_0)[answer_0 + 1U]) = status_10;
        step_0 = step_0 + 1U;
    }
    uint * _S100 = (&(globalParams_0->results_0)[output_0]);
    int _S101;
    if(status_10 == 0U)
    {
        _S101 = int(0);
    }
    else
    {
        _S101 = int(64);
    }
    *_S100 = uint(_S101);
    *(&(globalParams_0->results_0)[output_0 + 1U]) = _S80;
    *(&(globalParams_0->results_0)[output_0 + 2U]) = status_10;
    return;
}


// Transport ABI checks; shared arithmetic and event code above are unmodified.
static_assert(sizeof(Runtime_0) == 8, "Resident Runtime stride mismatch");
static_assert(alignof(Runtime_0) == 8, "Resident Runtime alignment mismatch");
