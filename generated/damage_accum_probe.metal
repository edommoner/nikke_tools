#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
uint daAt_0(uint base_0, uint object_0)
{
    return base_0 + object_0 * 24U;
}

struct Runtime_0
{
    ulong nextOrder_0;
};

struct KernelContext_0
{
    uint device* commands_0;
    Runtime_0 device* runtimeStates_0;
    uint device* results_0;
};

uint daFree_0(uint base_1, uint capacity_0, KernelContext_0 thread* kernelContext_0)
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
        if((*(kernelContext_0->results_0+(daAt_0(base_1, i_0) + 22U))) == 0U)
        {
            return i_0;
        }
        i_0 = i_0 + 1U;
    }
    return 4294967295U;
}

uint nextProbeOrder_0(uint id_0, KernelContext_0 thread* kernelContext_1)
{
    ulong next_0 = (kernelContext_1->runtimeStates_0+id_0)->nextOrder_0 + 1ULL;
    (kernelContext_1->runtimeStates_0+id_0)->nextOrder_0 = next_0;
    return uint(next_0);
}

ulong probeNumber_0(uint at_0, KernelContext_0 thread* kernelContext_2)
{
    return ulong(kernelContext_2->commands_0[at_0]) | (ulong(kernelContext_2->commands_0[at_0 + 1U]) << 32U);
}

bool f64Finite_0(ulong x_0)
{
    return (x_0 & 9223372036854775807ULL) < 9218868437227405312ULL;
}

void daUnlink_0(uint base_2, uint header_0, uint object_1, KernelContext_0 thread* kernelContext_3)
{
    uint at_1 = daAt_0(base_2, object_1);
    if(((*(kernelContext_3->results_0+(at_1 + 22U))) & 512U) == 0U)
    {
        return;
    }
    uint _S1 = at_1 + 7U;
    uint next_1 = *(kernelContext_3->results_0+_S1);
    uint _S2 = at_1 + 8U;
    uint device* _S3 = kernelContext_3->results_0+_S2;
    uint previous_0 = *_S3;
    if((*_S3) == 0U)
    {
        *(kernelContext_3->results_0+header_0) = next_1;
    }
    else
    {
        *(kernelContext_3->results_0+(daAt_0(base_2, previous_0 - 1U) + 7U)) = next_1;
    }
    if(next_1 == 0U)
    {
        *(kernelContext_3->results_0+(header_0 + 1U)) = previous_0;
    }
    else
    {
        *(kernelContext_3->results_0+(daAt_0(base_2, next_1 - 1U) + 8U)) = previous_0;
    }
    *(kernelContext_3->results_0+_S1) = 0U;
    *(kernelContext_3->results_0+_S2) = 0U;
    return;
}

void daStore_0(uint at_2, ulong value_0, KernelContext_0 thread* kernelContext_4)
{
    *(kernelContext_4->results_0+at_2) = uint(value_0);
    *(kernelContext_4->results_0+(at_2 + 1U)) = uint(value_0 >> 32U);
    return;
}

void daStore_1(uint at_3, ulong value_1, KernelContext_0 thread* kernelContext_5)
{
    *(kernelContext_5->results_0+at_3) = uint(value_1);
    *(kernelContext_5->results_0+(at_3 + 1U)) = uint(value_1 >> 32U);
    return;
}

void daLink_0(uint base_3, uint header_1, uint capacity_1, uint object_2, KernelContext_0 thread* kernelContext_6)
{
    uint at_4 = daAt_0(base_3, object_2);
    uint _S4 = *(kernelContext_6->results_0+(at_4 + 20U));
    uint next_2 = *(kernelContext_6->results_0+header_1);
    uint previous_1 = 0U;
    uint pass_0 = 0U;
    for(;;)
    {
        bool _S5;
        if(pass_0 < capacity_1)
        {
            _S5 = next_2 != 0U;
        }
        else
        {
            _S5 = false;
        }
        if(_S5)
        {
        }
        else
        {
            break;
        }
        uint _S6 = daAt_0(base_3, next_2 - 1U);
        if((*(kernelContext_6->results_0+(_S6 + 20U))) > _S4)
        {
            break;
        }
        uint _S7 = *(kernelContext_6->results_0+(_S6 + 7U));
        uint _S8 = pass_0 + 1U;
        previous_1 = next_2;
        next_2 = _S7;
        pass_0 = _S8;
    }
    *(kernelContext_6->results_0+(at_4 + 7U)) = next_2;
    *(kernelContext_6->results_0+(at_4 + 8U)) = previous_1;
    if(previous_1 == 0U)
    {
        *(kernelContext_6->results_0+header_1) = object_2 + 1U;
    }
    else
    {
        *(kernelContext_6->results_0+(daAt_0(base_3, previous_1 - 1U) + 7U)) = object_2 + 1U;
    }
    if(next_2 == 0U)
    {
        *(kernelContext_6->results_0+(header_1 + 1U)) = object_2 + 1U;
    }
    else
    {
        *(kernelContext_6->results_0+(daAt_0(base_3, next_2 - 1U) + 8U)) = object_2 + 1U;
    }
    return;
}

uint daArchive_0(uint base_4, uint capacity_2, uint name_0, bool create_0, uint thread* status_0, KernelContext_0 thread* kernelContext_7)
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
        uint at_5 = daAt_0(base_4, i_1);
        bool _S9;
        if(((*(kernelContext_7->results_0+(at_5 + 22U))) & 255U) == 14U)
        {
            _S9 = (*(kernelContext_7->results_0+(at_5 + 4U))) == name_0;
        }
        else
        {
            _S9 = false;
        }
        if(_S9)
        {
            return i_1;
        }
        i_1 = i_1 + 1U;
    }
    if(!create_0)
    {
        return 4294967295U;
    }
    uint _S10 = daFree_0(base_4, capacity_2, kernelContext_7);
    if(_S10 == 4294967295U)
    {
        *status_0 = 64U;
        return _S10;
    }
    uint at_6 = daAt_0(base_4, _S10);
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
        *(kernelContext_7->results_0+(at_6 + w_0)) = 0U;
        w_0 = w_0 + 1U;
    }
    *(kernelContext_7->results_0+(at_6 + 4U)) = name_0;
    *(kernelContext_7->results_0+(at_6 + 22U)) = 65550U;
    return _S10;
}

uint daArchive_1(uint base_5, uint capacity_3, uint name_1, bool create_1, uint thread* status_1, KernelContext_0 thread* kernelContext_8)
{
    *status_1 = 0U;
    uint i_2 = 0U;
    for(;;)
    {
        if(i_2 < capacity_3)
        {
        }
        else
        {
            break;
        }
        uint at_7 = daAt_0(base_5, i_2);
        bool _S11;
        if(((*(kernelContext_8->results_0+(at_7 + 22U))) & 255U) == 14U)
        {
            _S11 = (*(kernelContext_8->results_0+(at_7 + 4U))) == name_1;
        }
        else
        {
            _S11 = false;
        }
        if(_S11)
        {
            return i_2;
        }
        i_2 = i_2 + 1U;
    }
    if(!create_1)
    {
        return 4294967295U;
    }
    uint _S12 = daFree_0(base_5, capacity_3, kernelContext_8);
    if(_S12 == 4294967295U)
    {
        *status_1 = 64U;
        return _S12;
    }
    uint at_8 = daAt_0(base_5, _S12);
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
        *(kernelContext_8->results_0+(at_8 + w_1)) = 0U;
        w_1 = w_1 + 1U;
    }
    *(kernelContext_8->results_0+(at_8 + 4U)) = name_1;
    *(kernelContext_8->results_0+(at_8 + 22U)) = 65550U;
    return _S12;
}

void daRemember_0(uint base_6, uint capacity_4, uint name_2, ulong value_2, uint thread* status_2, KernelContext_0 thread* kernelContext_9)
{
    uint _S13 = daArchive_1(base_6, capacity_4, name_2, true, status_2, kernelContext_9);
    if((*status_2) == 0U)
    {
        daStore_1(daAt_0(base_6, _S13), value_2, kernelContext_9);
    }
    return;
}

void daInitializePool_0(uint base_7, uint capacity_5, uint header_2, uint object_3, uint name_3, uint owner_0, uint stat_0, uint order_0, uint slot_0, ulong cap_0, uint thread* status_3, KernelContext_0 thread* kernelContext_10)
{
    *status_3 = 0U;
    bool _S14;
    if(object_3 >= capacity_5)
    {
        _S14 = true;
    }
    else
    {
        _S14 = owner_0 >= 5U;
    }
    if(_S14)
    {
        _S14 = true;
    }
    else
    {
        if(stat_0 != 81U)
        {
            _S14 = stat_0 != 82U;
        }
        else
        {
            _S14 = false;
        }
    }
    if(_S14)
    {
        _S14 = true;
    }
    else
    {
        _S14 = order_0 == 0U;
    }
    if(_S14)
    {
        _S14 = true;
    }
    else
    {
        _S14 = !f64Finite_0(cap_0);
    }
    if(_S14)
    {
        *status_3 = 64U;
        return;
    }
    uint at_9 = daAt_0(base_7, object_3);
    daUnlink_0(base_7, header_2, object_3, kernelContext_10);
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
        *(kernelContext_10->results_0+(at_9 + w_2)) = 0U;
        w_2 = w_2 + 1U;
    }
    daStore_0(at_9 + 2U, cap_0, kernelContext_10);
    *(kernelContext_10->results_0+(at_9 + 4U)) = name_3;
    *(kernelContext_10->results_0+(at_9 + 20U)) = order_0;
    *(kernelContext_10->results_0+(at_9 + 21U)) = slot_0;
    uint device* _S15 = kernelContext_10->results_0+(at_9 + 22U);
    if(stat_0 == 81U)
    {
        w_2 = 13U;
    }
    else
    {
        w_2 = 16U;
    }
    *_S15 = ((w_2 | 512U) | 65536U) | (owner_0 << 10U);
    daLink_0(base_7, header_2, capacity_5, object_3, kernelContext_10);
    if(name_3 != 4294967295U)
    {
        daRemember_0(base_7, capacity_5, name_3, 0ULL, status_3, kernelContext_10);
    }
    return;
}

void daUpdateOwnerHP_0(uint base_8, uint capacity_6, uint owner_1, ulong hp_0, uint thread* status_4, KernelContext_0 thread* kernelContext_11)
{
    *status_4 = 0U;
    bool _S16;
    if(owner_1 >= 5U)
    {
        _S16 = true;
    }
    else
    {
        _S16 = !f64Finite_0(hp_0);
    }
    if(_S16)
    {
        *status_4 = 64U;
        return;
    }
    uint i_3 = 0U;
    for(;;)
    {
        if(i_3 < capacity_6)
        {
        }
        else
        {
            break;
        }
        uint at_10 = daAt_0(base_8, i_3);
        uint device* _S17 = kernelContext_11->results_0+(at_10 + 22U);
        uint flags_0 = *_S17;
        if(((*_S17) & 255U) == 15U)
        {
            _S16 = ((flags_0 >> 10U) & 7U) == owner_1;
        }
        else
        {
            _S16 = false;
        }
        if(_S16)
        {
            daStore_0(at_10 + 2U, hp_0, kernelContext_11);
        }
        i_3 = i_3 + 1U;
    }
    return;
}

void daInitializeRate_0(uint base_9, uint capacity_7, uint header_3, uint object_4, uint name_4, uint owner_2, uint order_1, uint policy_0, ulong value_3, uint stack_0, ulong hp_1, uint thread* status_5, KernelContext_0 thread* kernelContext_12)
{
    *status_5 = 0U;
    bool _S18;
    if(object_4 >= capacity_7)
    {
        _S18 = true;
    }
    else
    {
        _S18 = owner_2 >= 5U;
    }
    if(_S18)
    {
        _S18 = true;
    }
    else
    {
        _S18 = order_1 == 0U;
    }
    if(_S18)
    {
        _S18 = true;
    }
    else
    {
        _S18 = policy_0 > 15U;
    }
    if(_S18)
    {
        *status_5 = 64U;
        return;
    }
    if(!f64Finite_0(value_3))
    {
        _S18 = true;
    }
    else
    {
        _S18 = !f64Finite_0(hp_1);
    }
    if(_S18)
    {
        *status_5 = 16U;
        return;
    }
    uint at_11 = daAt_0(base_9, object_4);
    daUnlink_0(base_9, header_3, object_4, kernelContext_12);
    uint w_3 = 0U;
    for(;;)
    {
        if(w_3 < 24U)
        {
        }
        else
        {
            break;
        }
        *(kernelContext_12->results_0+(at_11 + w_3)) = 0U;
        w_3 = w_3 + 1U;
    }
    daStore_0(at_11, value_3, kernelContext_12);
    *(kernelContext_12->results_0+(at_11 + 4U)) = name_4;
    *(kernelContext_12->results_0+(at_11 + 5U)) = policy_0;
    *(kernelContext_12->results_0+(at_11 + 20U)) = order_1;
    *(kernelContext_12->results_0+(at_11 + 21U)) = stack_0;
    *(kernelContext_12->results_0+(at_11 + 22U)) = 66063U | (owner_2 << 10U);
    daLink_0(base_9, header_3, capacity_7, object_4, kernelContext_12);
    daUpdateOwnerHP_0(base_9, capacity_7, owner_2, hp_1, status_5, kernelContext_12);
    return;
}

bool f64Nan_0(ulong x_1)
{
    return (x_1 & 9223372036854775807ULL) > 9218868437227405312ULL;
}

bool f64Zero_0(ulong x_2)
{
    return (x_2 & 9223372036854775807ULL) == 0ULL;
}

bool f64Equal_0(ulong a_0, ulong b_0)
{
    bool _S19;
    if(!f64Nan_0(a_0))
    {
        _S19 = !f64Nan_0(b_0);
    }
    else
    {
        _S19 = false;
    }
    if(_S19)
    {
        if(a_0 == b_0)
        {
            _S19 = true;
        }
        else
        {
            if(f64Zero_0(a_0))
            {
                _S19 = f64Zero_0(b_0);
            }
            else
            {
                _S19 = false;
            }
        }
    }
    else
    {
        _S19 = false;
    }
    return _S19;
}

bool f64Less_0(ulong a_1, ulong b_1)
{
    bool _S20;
    if(f64Nan_0(a_1))
    {
        _S20 = true;
    }
    else
    {
        _S20 = f64Nan_0(b_1);
    }
    if(_S20)
    {
        _S20 = true;
    }
    else
    {
        _S20 = f64Equal_0(a_1, b_1);
    }
    if(_S20)
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
        _S20 = a_1 > b_1;
    }
    else
    {
        _S20 = a_1 < b_1;
    }
    return _S20;
}

ulong daNumber_0(uint at_12, KernelContext_0 thread* kernelContext_13)
{
    return ulong(*(kernelContext_13->results_0+at_12)) | (ulong(*(kernelContext_13->results_0+(at_12 + 1U))) << 32U);
}

ulong shiftJam_0(ulong x_3, uint distance_0)
{
    if(distance_0 == 0U)
    {
        return x_3;
    }
    int _S21;
    if(distance_0 >= 64U)
    {
        if(x_3 != 0ULL)
        {
            _S21 = int(1);
        }
        else
        {
            _S21 = int(0);
        }
        return ulong(_S21);
    }
    ulong _S22 = x_3 >> distance_0;
    if((x_3 << (64U - distance_0)) != 0ULL)
    {
        _S21 = int(1);
    }
    else
    {
        _S21 = int(0);
    }
    return _S22 | ulong(_S21);
}

ulong f64Pack_0(ulong sign_0, int exponent_0, ulong significand_0)
{
    bool _S23;
    if(significand_0 == 0ULL)
    {
        return sign_0;
    }
    ulong rounded_0;
    int _S24;
    if(significand_0 >= 72057594037927936ULL)
    {
        int _S25 = exponent_0 + int(1);
        rounded_0 = shiftJam_0(significand_0, 1U);
        _S24 = _S25;
    }
    else
    {
        rounded_0 = significand_0;
        _S24 = exponent_0;
    }
    for(;;)
    {
        if(rounded_0 < 36028797018963968ULL)
        {
            _S23 = _S24 > int(1);
        }
        else
        {
            _S23 = false;
        }
        if(_S23)
        {
        }
        else
        {
            break;
        }
        int _S26 = _S24 - int(1);
        rounded_0 = rounded_0 << 1U;
        _S24 = _S26;
    }
    if(_S24 < int(1))
    {
        rounded_0 = shiftJam_0(rounded_0, uint(int(1) - _S24));
        _S24 = int(1);
    }
    uint tail_0 = uint(rounded_0 & 7ULL);
    ulong rounded_1 = rounded_0 >> 3U;
    if(tail_0 > 4U)
    {
        _S23 = true;
    }
    else
    {
        if(tail_0 == 4U)
        {
            _S23 = (rounded_1 & 1ULL) != 0ULL;
        }
        else
        {
            _S23 = false;
        }
    }
    if(_S23)
    {
        rounded_0 = rounded_1 + 1ULL;
    }
    else
    {
        rounded_0 = rounded_1;
    }
    if(rounded_0 >= 9007199254740992ULL)
    {
        ulong rounded_2 = rounded_0 >> 1U;
        _S24 = _S24 + int(1);
        rounded_0 = rounded_2;
    }
    if(_S24 >= int(2047))
    {
        return sign_0 | 9218868437227405312ULL;
    }
    if(rounded_0 < 4503599627370496ULL)
    {
        _S24 = int(0);
    }
    return (sign_0 | (ulong(_S24) << 52U)) | (rounded_0 & 4503599627370495ULL);
}

ulong f64FromI64_0(ulong integer_0)
{
    ulong sign_1 = integer_0 & 9223372036854775808ULL;
    ulong magnitude_0;
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
    ulong scan_0 = magnitude_0;
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
        uint _S27 = highest_0 + 1U;
        scan_0 = scan_0 >> 1U;
        highest_0 = _S27;
    }
    ulong extended_0;
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

__attribute__((noinline))
ulong f64Add_0(ulong a_2, ulong b_2)
{
    bool _S28;
    if(f64Nan_0(a_2))
    {
        _S28 = true;
    }
    else
    {
        _S28 = f64Nan_0(b_2);
    }
    if(_S28)
    {
        return 9221120237041090560ULL;
    }
    ulong ma_0 = a_2 & 9223372036854775807ULL;
    ulong mb_0 = b_2 & 9223372036854775807ULL;
    bool _S29 = ma_0 == 9218868437227405312ULL;
    if(_S29)
    {
        _S28 = true;
    }
    else
    {
        _S28 = mb_0 == 9218868437227405312ULL;
    }
    ulong _S30;
    if(_S28)
    {
        if(ma_0 == mb_0)
        {
            _S28 = ((a_2 ^ b_2) & 9223372036854775808ULL) != 0ULL;
        }
        else
        {
            _S28 = false;
        }
        if(_S28)
        {
            return 9221120237041090560ULL;
        }
        if(_S29)
        {
            _S30 = a_2;
        }
        else
        {
            _S30 = b_2;
        }
        return _S30;
    }
    ulong _S31;
    if(ma_0 < mb_0)
    {
        _S30 = b_2;
        _S31 = a_2;
    }
    else
    {
        _S30 = a_2;
        _S31 = b_2;
    }
    ulong _S32 = _S30 & 4503599627370495ULL;
    ulong _S33 = (_S30 >> 52U) & 2047ULL;
    ulong _S34;
    if(_S33 != 0ULL)
    {
        _S34 = 4503599627370496ULL;
    }
    else
    {
        _S34 = 0ULL;
    }
    ulong sa_0 = _S32 | _S34;
    ulong _S35 = _S31 & 4503599627370495ULL;
    ulong _S36 = (_S31 >> 52U) & 2047ULL;
    if(_S36 != 0ULL)
    {
        _S34 = 4503599627370496ULL;
    }
    else
    {
        _S34 = 0ULL;
    }
    int _S37 = max(int(1), int(_S33));
    ulong sa_1 = sa_0 << 3U;
    ulong sb_0 = shiftJam_0((_S35 | _S34) << 3U, uint(_S37 - max(int(1), int(_S36))));
    if(((_S30 ^ _S31) & 9223372036854775808ULL) == 0ULL)
    {
        return f64Pack_0(_S30 & 9223372036854775808ULL, _S37, sa_1 + sb_0);
    }
    if(sa_1 == sb_0)
    {
        return 0ULL;
    }
    return f64Pack_0(_S30 & 9223372036854775808ULL, _S37, sa_1 - sb_0);
}

void f64Unpack_0(ulong bits_0, int thread* exponent_1, ulong thread* significand_1)
{
    *exponent_1 = int((bits_0 >> 52U) & 2047ULL);
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
            *significand_1 = (*significand_1) << 1U;
            *exponent_1 = *exponent_1 - int(1);
        }
    }
    return;
}

void f64Unpack_1(ulong bits_1, int thread* exponent_2, ulong thread* significand_2)
{
    *exponent_2 = int((bits_1 >> 52U) & 2047ULL);
    *significand_2 = bits_1 & 4503599627370495ULL;
    if((*exponent_2) != int(0))
    {
        *significand_2 = (*significand_2) | 4503599627370496ULL;
    }
    else
    {
        *exponent_2 = int(1);
        for(;;)
        {
            if((*significand_2) < 4503599627370496ULL)
            {
            }
            else
            {
                break;
            }
            *significand_2 = (*significand_2) << 1U;
            *exponent_2 = *exponent_2 - int(1);
        }
    }
    return;
}

void mulWide_0(ulong a_3, ulong b_3, ulong thread* hi_0, ulong thread* lo_0)
{
    ulong al_0 = ulong(uint(a_3));
    ulong ah_0 = a_3 >> 32U;
    ulong bl_0 = ulong(uint(b_3));
    ulong bh_0 = b_3 >> 32U;
    ulong p_0 = al_0 * bl_0;
    ulong middle_0 = ah_0 * bl_0 + (p_0 >> 32U);
    ulong middle_1 = ulong(uint(middle_0)) + al_0 * bh_0;
    *hi_0 = ah_0 * bh_0 + (middle_0 >> 32U) + (middle_1 >> 32U);
    *lo_0 = (middle_1 << 32U) | ulong(uint(p_0));
    return;
}

__attribute__((noinline))
ulong f64Mul_0(ulong a_4, ulong b_4)
{
    ulong sign_2 = (a_4 ^ b_4) & 9223372036854775808ULL;
    ulong ma_1 = a_4 & 9223372036854775807ULL;
    ulong mb_1 = b_4 & 9223372036854775807ULL;
    bool _S38;
    if(f64Nan_0(a_4))
    {
        _S38 = true;
    }
    else
    {
        _S38 = f64Nan_0(b_4);
    }
    if(_S38)
    {
        return 9221120237041090560ULL;
    }
    if(ma_1 == 9218868437227405312ULL)
    {
        _S38 = true;
    }
    else
    {
        _S38 = mb_1 == 9218868437227405312ULL;
    }
    if(_S38)
    {
        if(ma_1 == 0ULL)
        {
            _S38 = true;
        }
        else
        {
            _S38 = mb_1 == 0ULL;
        }
        ulong _S39;
        if(_S38)
        {
            _S39 = 9221120237041090560ULL;
        }
        else
        {
            _S39 = sign_2 | 9218868437227405312ULL;
        }
        return _S39;
    }
    if(ma_1 == 0ULL)
    {
        _S38 = true;
    }
    else
    {
        _S38 = mb_1 == 0ULL;
    }
    if(_S38)
    {
        return sign_2;
    }
    thread int ea_0;
    thread ulong sa_2;
    f64Unpack_0(a_4, &ea_0, &sa_2);
    thread int eb_0;
    thread ulong sb_1;
    f64Unpack_0(b_4, &eb_0, &sb_1);
    thread ulong hi_1;
    thread ulong lo_1;
    mulWide_0(sa_2, sb_1, &hi_1, &lo_1);
    ulong sig_0 = (hi_1 << 15U) | (lo_1 >> 49U);
    int _S40;
    if((lo_1 << 15U) != 0ULL)
    {
        _S40 = int(1);
    }
    else
    {
        _S40 = int(0);
    }
    return f64Pack_0(sign_2, ea_0 + eb_0 - int(1023), sig_0 | ulong(_S40));
}

ulong daRate_0(uint base_10, uint capacity_8, uint header_4, uint pool_0, uint thread* status_6, KernelContext_0 thread* kernelContext_14)
{
    *status_6 = 0U;
    uint p_1 = daAt_0(base_10, pool_0);
    uint _S41 = ((*(kernelContext_14->results_0+(p_1 + 22U))) >> 10U) & 7U;
    uint _S42 = *(kernelContext_14->results_0+(p_1 + 4U));
    uint next_3 = *(kernelContext_14->results_0+header_4);
    ulong baseline_0 = 0ULL;
    ulong add_0 = 0ULL;
    bool present_0 = false;
    uint pass_1 = 0U;
    for(;;)
    {
        bool _S43;
        if(pass_1 < capacity_8)
        {
            _S43 = next_3 != 0U;
        }
        else
        {
            _S43 = false;
        }
        if(_S43)
        {
        }
        else
        {
            break;
        }
        uint at_13 = daAt_0(base_10, next_3 - 1U);
        uint device* _S44 = kernelContext_14->results_0+(at_13 + 22U);
        uint flags_1 = *_S44;
        uint _S45 = *(kernelContext_14->results_0+(at_13 + 7U));
        bool _S46;
        if(((*_S44) & 255U) != 15U)
        {
            _S46 = true;
        }
        else
        {
            _S46 = ((flags_1 >> 10U) & 7U) != _S41;
        }
        if(_S46)
        {
            uint _S47 = pass_1 + 1U;
            next_3 = _S45;
            pass_1 = _S47;
            continue;
        }
        uint device* _S48 = kernelContext_14->results_0+(at_13 + 5U);
        uint policy_1 = *_S48;
        if(((*_S48) & 1U) == 0U)
        {
            uint _S47 = pass_1 + 1U;
            next_3 = _S45;
            pass_1 = _S47;
            continue;
        }
        ulong _S49 = daNumber_0(at_13, kernelContext_14);
        ulong value_4;
        if((policy_1 & 4U) != 0U)
        {
            ulong _S50 = f64FromI64_0(100ULL);
            ulong _S51 = daNumber_0(at_13 + 2U, kernelContext_14);
            ulong lost_0 = f64Add_0(_S50, _S51 ^ 9223372036854775808ULL);
            if(f64Less_0(lost_0, 0ULL))
            {
                value_4 = 0ULL;
            }
            else
            {
                value_4 = lost_0;
            }
            value_4 = f64Mul_0(_S49, value_4);
        }
        else
        {
            if((policy_1 & 8U) != 0U)
            {
                value_4 = f64Mul_0(_S49, f64FromI64_0(ulong(*(kernelContext_14->results_0+(at_13 + 21U)))));
            }
            else
            {
                value_4 = _S49;
            }
        }
        if(!f64Finite_0(value_4))
        {
            *status_6 = 16U;
            return 0ULL;
        }
        ulong baseline_1;
        ulong add_1;
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
            if((*(kernelContext_14->results_0+(at_13 + 4U))) == _S42)
            {
                baseline_1 = f64Add_0(add_0, value_4);
            }
            else
            {
                baseline_1 = add_0;
            }
            ulong _S52 = baseline_1;
            baseline_1 = baseline_0;
            add_1 = _S52;
            present_1 = present_0;
        }
        baseline_0 = baseline_1;
        add_0 = add_1;
        present_0 = present_1;
        uint _S47 = pass_1 + 1U;
        next_3 = _S45;
        pass_1 = _S47;
    }
    if(present_0)
    {
    }
    else
    {
        baseline_0 = f64FromI64_0(100ULL);
    }
    ulong rate_0 = f64Add_0(baseline_0, add_0);
    if(!f64Finite_0(rate_0))
    {
        *status_6 = 16U;
    }
    return rate_0;
}

__attribute__((noinline))
ulong f64Div_0(ulong a_5, ulong b_5)
{
    ulong sign_3 = (a_5 ^ b_5) & 9223372036854775808ULL;
    ulong ma_2 = a_5 & 9223372036854775807ULL;
    ulong mb_2 = b_5 & 9223372036854775807ULL;
    bool _S53;
    if(f64Nan_0(a_5))
    {
        _S53 = true;
    }
    else
    {
        _S53 = f64Nan_0(b_5);
    }
    if(_S53)
    {
        _S53 = true;
    }
    else
    {
        if(ma_2 == 9218868437227405312ULL)
        {
            _S53 = mb_2 == 9218868437227405312ULL;
        }
        else
        {
            _S53 = false;
        }
    }
    if(_S53)
    {
        _S53 = true;
    }
    else
    {
        if(ma_2 == 0ULL)
        {
            _S53 = mb_2 == 0ULL;
        }
        else
        {
            _S53 = false;
        }
    }
    if(_S53)
    {
        return 9221120237041090560ULL;
    }
    if(ma_2 == 9218868437227405312ULL)
    {
        _S53 = true;
    }
    else
    {
        _S53 = mb_2 == 0ULL;
    }
    if(_S53)
    {
        return sign_3 | 9218868437227405312ULL;
    }
    if(ma_2 == 0ULL)
    {
        _S53 = true;
    }
    else
    {
        _S53 = mb_2 == 9218868437227405312ULL;
    }
    if(_S53)
    {
        return sign_3;
    }
    thread int ea_1;
    thread ulong remainder_0;
    f64Unpack_1(a_5, &ea_1, &remainder_0);
    thread int eb_1;
    thread ulong divisor_0;
    f64Unpack_1(b_5, &eb_1, &divisor_0);
    int exponent_3 = ea_1 - eb_1 + int(1023);
    int exponent_4;
    if(remainder_0 < divisor_0)
    {
        remainder_0 = remainder_0 << 1U;
        exponent_4 = exponent_3 - int(1);
    }
    else
    {
        exponent_4 = exponent_3;
    }
    uint bit_0 = 0U;
    ulong sig_1 = 0ULL;
    for(;;)
    {
        if(bit_0 < 56U)
        {
        }
        else
        {
            break;
        }
        ulong sig_2 = sig_1 << 1U;
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
            remainder_0 = remainder_0 << 1U;
        }
        bit_0 = bit_0 + 1U;
    }
    int _S54;
    if(remainder_0 != 0ULL)
    {
        _S54 = int(1);
    }
    else
    {
        _S54 = int(0);
    }
    return f64Pack_0(sign_3, exponent_4, sig_1 | ulong(_S54));
}

uint daCollect_0(uint base_11, uint capacity_9, uint header_5, uint owner_3, ulong damage_0, uint queue_0, uint queueCapacity_0, uint thread* status_7, KernelContext_0 thread* kernelContext_15)
{
    *status_7 = 0U;
    if(!f64Finite_0(damage_0))
    {
        *status_7 = 16U;
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
        uint _S55 = *(kernelContext_15->results_0+header_5);
        uint _S56;
        if(group_0 == 0U)
        {
            _S56 = 13U;
        }
        else
        {
            _S56 = 16U;
        }
        uint next_4 = _S55;
        uint pass_2 = 0U;
        uint count_1 = count_0;
        for(;;)
        {
            bool _S57;
            if(pass_2 < capacity_9)
            {
                _S57 = next_4 != 0U;
            }
            else
            {
                _S57 = false;
            }
            if(_S57)
            {
            }
            else
            {
                break;
            }
            uint chosen_0 = next_4 - 1U;
            uint at_14 = daAt_0(base_11, chosen_0);
            uint _S58 = at_14 + 22U;
            uint device* _S59 = kernelContext_15->results_0+_S58;
            uint flags_2 = *_S59;
            uint _S60 = *(kernelContext_15->results_0+(at_14 + 7U));
            uint count_2;
            if(((*_S59) & 255U) != _S56)
            {
                count_2 = count_1;
                uint _S61 = pass_2 + 1U;
                next_4 = _S60;
                pass_2 = _S61;
                count_1 = count_2;
                continue;
            }
            uint caster_0 = (flags_2 >> 10U) & 7U;
            ulong _S62 = daNumber_0(at_14 + 2U, kernelContext_15);
            bool _S63;
            if((flags_2 & 262144U) != 0U)
            {
                _S63 = true;
            }
            else
            {
                _S63 = !f64Less_0(0ULL, _S62);
            }
            bool _S64;
            if(_S63)
            {
                _S64 = true;
            }
            else
            {
                if(_S56 == 13U)
                {
                    _S64 = caster_0 != owner_3;
                }
                else
                {
                    _S64 = false;
                }
            }
            if(_S64)
            {
                count_2 = count_1;
                uint _S61 = pass_2 + 1U;
                next_4 = _S60;
                pass_2 = _S61;
                count_1 = count_2;
                continue;
            }
            ulong _S65 = daRate_0(base_11, capacity_9, header_5, chosen_0, status_7, kernelContext_15);
            if((*status_7) != 0U)
            {
                return count_1;
            }
            ulong _S66 = daNumber_0(at_14, kernelContext_15);
            ulong current_0 = f64Add_0(_S66, f64Div_0(f64Mul_0(damage_0, _S65), f64FromI64_0(100ULL)));
            ulong current_1;
            if(f64Less_0(_S62, current_0))
            {
                current_1 = _S62;
            }
            else
            {
                current_1 = current_0;
            }
            if(!f64Finite_0(current_1))
            {
                *status_7 = 16U;
                return count_1;
            }
            daStore_0(at_14, current_1, kernelContext_15);
            uint device* _S67 = kernelContext_15->results_0+(at_14 + 4U);
            uint name_5 = *_S67;
            bool _S68 = (*_S67) != 4294967295U;
            if(_S68)
            {
                daRemember_0(base_11, capacity_9, name_5, current_1, status_7, kernelContext_15);
                if((*status_7) != 0U)
                {
                    return count_1;
                }
            }
            if(!f64Less_0(current_1, f64Add_0(_S62, 13695778570484766357ULL)))
            {
                uint device* _S69 = kernelContext_15->results_0+_S58;
                *_S69 = (*_S69) | 262144U;
                if(_S68)
                {
                    if(count_1 >= queueCapacity_0)
                    {
                        *status_7 = 64U;
                        return count_1;
                    }
                    uint _S70 = queue_0 + count_1 * 2U;
                    *(kernelContext_15->results_0+_S70) = name_5;
                    *(kernelContext_15->results_0+(_S70 + 1U)) = caster_0;
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
            uint _S61 = pass_2 + 1U;
            next_4 = _S60;
            pass_2 = _S61;
            count_1 = count_2;
        }
        group_0 = group_0 + 1U;
        count_0 = count_1;
    }
    return count_0;
}

bool daPool_0(uint flags_3)
{
    uint _S71 = flags_3 & 255U;
    bool _S72;
    if(_S71 == 13U)
    {
        _S72 = true;
    }
    else
    {
        _S72 = _S71 == 16U;
    }
    return _S72;
}

ulong daTake_0(uint base_12, uint capacity_10, uint header_6, uint name_6, uint thread* status_8, KernelContext_0 thread* kernelContext_16)
{
    uint chosen_1;
    *status_8 = 0U;
    uint next_5 = *(kernelContext_16->results_0+header_6);
    uint pass_3 = 0U;
    for(;;)
    {
        bool _S73;
        if(pass_3 < capacity_10)
        {
            _S73 = next_5 != 0U;
        }
        else
        {
            _S73 = false;
        }
        if(_S73)
        {
        }
        else
        {
            chosen_1 = 4294967295U;
            break;
        }
        uint object_5 = next_5 - 1U;
        uint at_15 = daAt_0(base_12, object_5);
        uint _S74 = *(kernelContext_16->results_0+(at_15 + 7U));
        bool _S75;
        if(daPool_0(*(kernelContext_16->results_0+(at_15 + 22U))))
        {
            _S75 = (*(kernelContext_16->results_0+(at_15 + 4U))) == name_6;
        }
        else
        {
            _S75 = false;
        }
        if(_S75)
        {
            chosen_1 = object_5;
            break;
        }
        uint _S76 = pass_3 + 1U;
        next_5 = _S74;
        pass_3 = _S76;
    }
    ulong value_5;
    if(chosen_1 != 4294967295U)
    {
        uint at_16 = daAt_0(base_12, chosen_1);
        ulong _S77 = daNumber_0(at_16, kernelContext_16);
        daStore_0(at_16, 0ULL, kernelContext_16);
        uint device* _S78 = kernelContext_16->results_0+(at_16 + 22U);
        *_S78 = (*_S78) | 262144U;
        value_5 = _S77;
    }
    else
    {
        uint _S79 = daArchive_0(base_12, capacity_10, name_6, false, status_8, kernelContext_16);
        if(_S79 != 4294967295U)
        {
            ulong _S80 = daNumber_0(daAt_0(base_12, _S79), kernelContext_16);
            value_5 = _S80;
        }
        else
        {
            value_5 = 0ULL;
        }
    }
    daRemember_0(base_12, capacity_10, name_6, 0ULL, status_8, kernelContext_16);
    return value_5;
}

ulong f64Abs_0(ulong x_4)
{
    return x_4 & 9223372036854775807ULL;
}

ulong f64Integral_0(ulong x_5, uint mode_0)
{
    ulong magnitude_1 = f64Abs_0(x_5);
    ulong sign_4 = x_5 & 9223372036854775808ULL;
    if(f64Nan_0(x_5))
    {
        return 9221120237041090560ULL;
    }
    int exponent_5 = int((x_5 >> 52U) & 2047ULL) - int(1023);
    bool one_0;
    if(exponent_5 >= int(52))
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
    ulong rounded_3;
    if(exponent_5 < int(0))
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
    ulong unit_0 = 1ULL << uint(int(52) - exponent_5);
    ulong mask_0 = unit_0 - 1ULL;
    ulong tail_1 = magnitude_1 & mask_0;
    ulong rounded_4 = magnitude_1 & (~mask_0);
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
            ulong _S81 = unit_0 >> 1U;
            if(tail_1 > _S81)
            {
                one_0 = true;
            }
            else
            {
                if(tail_1 == _S81)
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

ulong f64ToI64_0(ulong x_6, uint mode_1, uint thread* status_9)
{
    *status_9 = 0U;
    if(!f64Finite_0(x_6))
    {
        *status_9 = 1U;
        return 0ULL;
    }
    ulong rounded_5 = f64Integral_0(x_6, mode_1);
    if((f64Abs_0(rounded_5)) == 0ULL)
    {
        return 0ULL;
    }
    int exponent_6 = int((rounded_5 >> 52U) & 2047ULL) - int(1023);
    bool negative_0 = (rounded_5 & 9223372036854775808ULL) != 0ULL;
    bool _S82;
    if(exponent_6 > int(63))
    {
        _S82 = true;
    }
    else
    {
        if(exponent_6 == int(63))
        {
            if(!negative_0)
            {
                _S82 = true;
            }
            else
            {
                _S82 = (rounded_5 & 4503599627370495ULL) != 0ULL;
            }
        }
        else
        {
            _S82 = false;
        }
    }
    if(_S82)
    {
        *status_9 = 1U;
        return 0ULL;
    }
    if(exponent_6 < int(0))
    {
        return 0ULL;
    }
    ulong significand_3 = (rounded_5 & 4503599627370495ULL) | 4503599627370496ULL;
    ulong integer_1;
    if(exponent_6 >= int(52))
    {
        integer_1 = significand_3 << uint(exponent_6 - int(52));
    }
    else
    {
        integer_1 = significand_3 >> uint(int(52) - exponent_6);
    }
    if(negative_0)
    {
        integer_1 = ~integer_1 + 1ULL;
    }
    return integer_1;
}

ulong daEmission_0(ulong amount_0, ulong split_0, bool thread* emit_0, uint thread* status_10)
{
    *emit_0 = false;
    *status_10 = 0U;
    bool _S83;
    if(!f64Finite_0(amount_0))
    {
        _S83 = true;
    }
    else
    {
        _S83 = !f64Finite_0(split_0);
    }
    if(_S83)
    {
        *status_10 = 16U;
        return 0ULL;
    }
    if(!f64Less_0(0ULL, amount_0))
    {
        return 0ULL;
    }
    *emit_0 = true;
    thread uint conversion_0;
    ulong integer_2 = f64ToI64_0(f64Mul_0(amount_0, f64Add_0(f64FromI64_0(1ULL), f64Div_0(split_0, f64FromI64_0(100ULL)))), 1U, &conversion_0);
    if(conversion_0 != 0U)
    {
        *status_10 = 16U;
        return 0ULL;
    }
    return integer_2;
}

void daRetire_0(uint base_13, uint header_7, uint object_6, KernelContext_0 thread* kernelContext_17)
{
    daUnlink_0(base_13, header_7, object_6, kernelContext_17);
    *(kernelContext_17->results_0+(daAt_0(base_13, object_6) + 22U)) = 0U;
    return;
}

[[kernel]] void portableEvents(uint3 id_1 [[thread_position_in_grid]], uint device* commands_1 [[buffer(0)]], Runtime_0 device* runtimeStates_1 [[buffer(2)]], uint device* results_1 [[buffer(1)]])
{
    bool _S84;
    uint object_7;
    thread KernelContext_0 kernelContext_18;
    (&kernelContext_18)->commands_0 = commands_1;
    (&kernelContext_18)->runtimeStates_0 = runtimeStates_1;
    (&kernelContext_18)->results_0 = results_1;
    uint _S85 = id_1.x;
    if(_S85 >= commands_1[int(0)])
    {
        return;
    }
    uint input_0 = 1U + _S85 * 512U;
    uint output_0 = _S85 * 786432U;
    uint _S86 = output_0 + 16U;
    uint header_8 = output_0 + 8U;
    thread uint status_11 = 0U;
    ((&kernelContext_18)->runtimeStates_0+_S85)->nextOrder_0 = 0ULL;
    uint capacity_11 = (&kernelContext_18)->commands_0[input_0];
    uint count_3 = (&kernelContext_18)->commands_0[input_0 + 1U];
    bool _S87;
    if(capacity_11 == 0U)
    {
        _S87 = true;
    }
    else
    {
        _S87 = capacity_11 > 32U;
    }
    if(_S87)
    {
        _S87 = true;
    }
    else
    {
        _S87 = count_3 > 24U;
    }
    if(_S87)
    {
        *((&kernelContext_18)->results_0+output_0) = 64U;
        return;
    }
    *((&kernelContext_18)->results_0+header_8) = 0U;
    *((&kernelContext_18)->results_0+(header_8 + 1U)) = 0U;
    uint i_4 = 0U;
    for(;;)
    {
        if(i_4 < 768U)
        {
        }
        else
        {
            break;
        }
        *((&kernelContext_18)->results_0+(_S86 + i_4)) = 0U;
        i_4 = i_4 + 1U;
    }
    uint step_0 = 0U;
    for(;;)
    {
        if(step_0 < count_3)
        {
            _S87 = status_11 == 0U;
        }
        else
        {
            _S87 = false;
        }
        if(_S87)
        {
        }
        else
        {
            break;
        }
        uint at_17 = input_0 + 2U + step_0 * 20U;
        uint op_0 = (&kernelContext_18)->commands_0[at_17];
        uint logical_0 = (&kernelContext_18)->commands_0[at_17 + 1U];
        uint answer_0 = output_0 + 1024U + step_0 * 32U;
        *((&kernelContext_18)->results_0+answer_0) = op_0;
        i_4 = 0U;
        for(;;)
        {
            if(i_4 < capacity_11)
            {
            }
            else
            {
                object_7 = 4294967295U;
                break;
            }
            uint p_2 = daAt_0(_S86, i_4);
            if(((*((&kernelContext_18)->results_0+(p_2 + 22U))) & 512U) != 0U)
            {
                _S84 = (*((&kernelContext_18)->results_0+(p_2 + 6U))) == logical_0;
            }
            else
            {
                _S84 = false;
            }
            if(_S84)
            {
                object_7 = i_4;
                break;
            }
            i_4 = i_4 + 1U;
        }
        bool _S88 = op_0 == 0U;
        if(_S88)
        {
            _S84 = true;
        }
        else
        {
            _S84 = op_0 == 1U;
        }
        uint object_8;
        if(_S84)
        {
            if(object_7 == 4294967295U)
            {
                uint _S89 = daFree_0(_S86, capacity_11, &kernelContext_18);
                object_8 = _S89;
            }
            else
            {
                object_8 = object_7;
            }
            if(object_8 == 4294967295U)
            {
                status_11 = 64U;
                break;
            }
            uint p_3 = daAt_0(_S86, object_8);
            if(_S88)
            {
                uint _S90 = (&kernelContext_18)->commands_0[at_17 + 3U];
                uint _S91 = (&kernelContext_18)->commands_0[at_17 + 4U];
                uint _S92 = (&kernelContext_18)->commands_0[at_17 + 2U];
                uint _S93 = nextProbeOrder_0(_S85, &kernelContext_18);
                ulong _S94 = probeNumber_0(at_17 + 5U, &kernelContext_18);
                daInitializePool_0(_S86, capacity_11, header_8, object_8, _S90, _S91, _S92, _S93, logical_0, _S94, &status_11, &kernelContext_18);
            }
            else
            {
                uint _S95 = (&kernelContext_18)->commands_0[at_17 + 3U];
                uint _S96 = (&kernelContext_18)->commands_0[at_17 + 4U];
                uint _S97 = nextProbeOrder_0(_S85, &kernelContext_18);
                uint _S98 = (&kernelContext_18)->commands_0[at_17 + 2U];
                ulong _S99 = probeNumber_0(at_17 + 5U, &kernelContext_18);
                uint _S100 = (&kernelContext_18)->commands_0[at_17 + 7U];
                ulong _S101 = probeNumber_0(at_17 + 9U, &kernelContext_18);
                daInitializeRate_0(_S86, capacity_11, header_8, object_8, _S95, _S96, _S97, _S98, _S99, _S100, _S101, &status_11, &kernelContext_18);
            }
            *((&kernelContext_18)->results_0+(p_3 + 6U)) = logical_0;
        }
        else
        {
            if(op_0 == 2U)
            {
                uint queue_1 = output_0 + 3072U;
                ulong _S102 = probeNumber_0(at_17 + 5U, &kernelContext_18);
                uint _S103 = daCollect_0(_S86, capacity_11, header_8, logical_0, _S102, queue_1, 8U, &status_11, &kernelContext_18);
                *((&kernelContext_18)->results_0+(answer_0 + 5U)) = _S103;
                object_8 = 0U;
                for(;;)
                {
                    if(object_8 < _S103)
                    {
                    }
                    else
                    {
                        break;
                    }
                    uint _S104 = object_8 * 2U;
                    uint _S105 = queue_1 + _S104;
                    *((&kernelContext_18)->results_0+(answer_0 + 6U + _S104)) = *((&kernelContext_18)->results_0+_S105);
                    *((&kernelContext_18)->results_0+(answer_0 + 7U + _S104)) = *((&kernelContext_18)->results_0+(_S105 + 1U));
                    object_8 = object_8 + 1U;
                }
                uint i_5 = 0U;
                uint done_0 = 0U;
                for(;;)
                {
                    if(i_5 < capacity_11)
                    {
                    }
                    else
                    {
                        break;
                    }
                    uint p_4 = daAt_0(_S86, i_5);
                    uint _S106 = p_4 + 22U;
                    bool _S107;
                    if(daPool_0(*((&kernelContext_18)->results_0+_S106)))
                    {
                        _S107 = ((*((&kernelContext_18)->results_0+_S106)) & 262144U) != 0U;
                    }
                    else
                    {
                        _S107 = false;
                    }
                    if(_S107)
                    {
                        done_0 = done_0 | (1U << (*((&kernelContext_18)->results_0+(p_4 + 6U))));
                    }
                    i_5 = i_5 + 1U;
                }
                *((&kernelContext_18)->results_0+(answer_0 + 22U)) = done_0;
            }
            else
            {
                if(op_0 == 3U)
                {
                    ulong _S108 = daTake_0(_S86, capacity_11, header_8, (&kernelContext_18)->commands_0[at_17 + 3U], &status_11, &kernelContext_18);
                    daStore_0(answer_0 + 2U, _S108, &kernelContext_18);
                    ulong _S109 = probeNumber_0(at_17 + 5U, &kernelContext_18);
                    thread bool emit_1;
                    thread uint convert_0;
                    ulong integer_3 = daEmission_0(_S108, _S109, &emit_1, &convert_0);
                    if(status_11 == 0U)
                    {
                        status_11 = convert_0;
                    }
                    *((&kernelContext_18)->results_0+(answer_0 + 4U)) = uint(emit_1);
                    daStore_0(answer_0 + 24U, integer_3, &kernelContext_18);
                }
                else
                {
                    if(op_0 == 4U)
                    {
                        if(object_7 == 4294967295U)
                        {
                            status_11 = 64U;
                        }
                        else
                        {
                            daRetire_0(_S86, header_8, object_7, &kernelContext_18);
                        }
                    }
                    else
                    {
                        if(op_0 == 5U)
                        {
                            if(object_7 == 4294967295U)
                            {
                                status_11 = 64U;
                            }
                            else
                            {
                                ulong _S110 = daRate_0(_S86, capacity_11, header_8, object_7, &status_11, &kernelContext_18);
                                daStore_0(answer_0 + 2U, _S110, &kernelContext_18);
                            }
                        }
                        else
                        {
                            if(op_0 == 6U)
                            {
                                ulong _S111 = probeNumber_0(at_17 + 5U, &kernelContext_18);
                                daUpdateOwnerHP_0(_S86, capacity_11, logical_0, _S111, &status_11, &kernelContext_18);
                            }
                            else
                            {
                                status_11 = 64U;
                            }
                        }
                    }
                }
            }
        }
        *((&kernelContext_18)->results_0+(answer_0 + 1U)) = status_11;
        step_0 = step_0 + 1U;
    }
    uint device* _S112 = (&kernelContext_18)->results_0+output_0;
    int _S113;
    if(status_11 == 0U)
    {
        _S113 = int(0);
    }
    else
    {
        _S113 = int(64);
    }
    *_S112 = uint(_S113);
    *((&kernelContext_18)->results_0+(output_0 + 1U)) = count_3;
    *((&kernelContext_18)->results_0+(output_0 + 2U)) = status_11;
    return;
}

